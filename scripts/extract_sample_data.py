"""
Extract a small number of real samples from the full Karman datasets and save
them as a compact .pt file that inference_simple_tft.py can load directly.

This script needs to be run once.  It instantiates the full KarmanDataset
(which loads multi-GB CSVs into memory) and then cherry-picks N samples,
constructing exactly the same tensors the training loop feeds into the TFT.

Usage:
    python scripts/extract_sample_data.py \
        --data_dir /Users/wfawcett/Documents/trillium/data/data_for_2024_tft_model \
        --n_samples 10 \
        --output data/sample_inputs.pt
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
import pandas as pd
import numpy as np
import karman

# ── Parameters matching the trained model ─────────────────────────────────────
# Model: ts_karman_model_tft_run_gpu_tft_w_omni_and_soho_wo_indices_and_proxies
#        _w_10000_lag_100_resolution_valid_mape_14.936_params_1074865.torch
#
# "wo_indices_and_proxies" → exclude solar/geomag index columns from static
LAG_MINUTES = 10_000
RESOLUTION_MINUTES = 100

# These are the thermo features excluded during training ("wo_indices_and_proxies")
FEATURES_TO_EXCLUDE_THERMO = [
    "all__dates_datetime__",
    "tudelft_thermo__satellite__",
    "tudelft_thermo__ground_truth_thermospheric_density__[kg/m**3]",
    "all__year__[y]",
    "NRLMSISE00__thermospheric_density__[kg/m**3]",
    # "wo_indices_and_proxies":
    "celestrack__ap_average__",
    "space_environment_technologies__f107_obs__",
    "space_environment_technologies__f107_average__",
    "space_environment_technologies__s107_obs__",
    "space_environment_technologies__s107_average__",
    "space_environment_technologies__m107_obs__",
    "space_environment_technologies__m107_average__",
    "space_environment_technologies__y107_obs__",
    "space_environment_technologies__y107_average__",
    "JB08__d_st_dt__[K]",
]


def main():
    parser = argparse.ArgumentParser(
        description="Extract sample inputs from the full Karman datasets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data_dir",
        default="/Users/wfawcett/Documents/trillium/data/data_for_2024_tft_model",
        help="Directory containing the CSV files",
    )
    parser.add_argument(
        "--n_samples", type=int, default=10, help="Number of samples to extract"
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "sample_inputs_tft.pt"),
        help="Output .pt file path",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for sample selection"
    )
    args = parser.parse_args()

    data_dir = args.data_dir
    thermo_path = os.path.join(data_dir, "satellites_data_w_sw_2mln.csv")
    omni_indices_path = os.path.join(data_dir, "merged_omni_indices.csv")
    omni_magnetic_field_path = os.path.join(data_dir, "merged_omni_magnetic_field.csv")
    omni_solar_wind_path = os.path.join(data_dir, "merged_omni_solar_wind.csv")
    soho_path = os.path.join(data_dir, "soho_data.csv")
    nrlmsise00_path = os.path.join(data_dir, "nrlmsise00_time_series.csv")

    print("Loading KarmanDataset (this may take several minutes due to large files)...")
    dataset = karman.KarmanDataset(
        thermo_path=thermo_path,
        omni_indices_path=omni_indices_path,
        omni_magnetic_field_path=omni_magnetic_field_path,
        omni_solar_wind_path=omni_solar_wind_path,
        soho_path=soho_path,
        nrlmsise00_path=nrlmsise00_path,
        lag_minutes_omni=LAG_MINUTES,
        omni_resolution=RESOLUTION_MINUTES,
        lag_minutes_soho=LAG_MINUTES,
        soho_resolution=RESOLUTION_MINUTES,
        lag_minutes_nrlmsise00=LAG_MINUTES,
        nrlmsise00_resolution=RESOLUTION_MINUTES,
        features_to_exclude_thermo=FEATURES_TO_EXCLUDE_THERMO,
        min_date=pd.to_datetime("2000-07-29 00:59:47"),
        max_date=pd.to_datetime("2024-05-31 23:59:32"),
        exclude_mask="exclude_mask.pk",
    )
    print(f"Dataset size: {len(dataset)} observations")

    # Pick N evenly-spaced indices so we cover a range of conditions
    np.random.seed(args.seed)
    total = len(dataset)
    if args.n_samples >= total:
        indices = list(range(total))
    else:
        indices = sorted(np.random.choice(total, size=args.n_samples, replace=False).tolist())

    print(f"Extracting {len(indices)} samples at indices: {indices}")

    # Collect samples, building tensors exactly as the training loop does
    static_list = []
    historical_list = []
    future_list = []
    target_list = []
    ground_truth_list = []
    nrlmsise00_list = []
    date_list = []

    for i, idx in enumerate(indices):
        sample = dataset[idx]
        # Static features
        static_list.append(sample["instantaneous_features"])
        # Historical: concat [omni_indices, omni_magnetic_field, omni_solar_wind, soho, msise] [:,:-1,:]
        hist_parts = []
        for key in ["omni_indices", "omni_magnetic_field", "omni_solar_wind", "soho", "msise"]:
            hist_parts.append(sample[key][:-1, :])  # drop last timestep
        historical_list.append(torch.cat(hist_parts, dim=1))
        # Future: last timestep of msise, keep only first column (model uses num_future_numeric=1)
        future_list.append(sample["msise"][-1, :1].unsqueeze(0))  # shape (1, 1)
        # Targets & metadata
        target_list.append(sample["target"])
        ground_truth_list.append(sample["ground_truth"])
        nrlmsise00_list.append(sample["nrlmsise00"])
        date_list.append(sample["date"])
        print(f"  [{i+1}/{len(indices)}] date={sample['date']}, "
              f"storm={sample['geomagnetic_storm_G_class']}, "
              f"alt_bin={sample['altitude_bins']}")

    # Stack into batch tensors
    payload = {
        "static_feats_numeric": torch.stack(static_list),       # (N, 8)
        "historical_ts_numeric": torch.stack(historical_list),   # (N, 100, 25)
        "future_ts_numeric": torch.stack(future_list),           # (N, 1, 1)
        "target": torch.stack(target_list),                      # (N,)
        "ground_truth": torch.stack(ground_truth_list),          # (N,)
        "nrlmsise00": torch.stack(nrlmsise00_list),              # (N,)
        "dates": date_list,
        "normalization_dict": dataset.normalization_dict,
    }

    # Verify shapes
    print(f"\nTensor shapes:")
    print(f"  static_feats_numeric:  {payload['static_feats_numeric'].shape}")
    print(f"  historical_ts_numeric: {payload['historical_ts_numeric'].shape}")
    print(f"  future_ts_numeric:     {payload['future_ts_numeric'].shape}")
    print(f"  target:                {payload['target'].shape}")
    print(f"  ground_truth:          {payload['ground_truth'].shape}")

    # Save
    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    torch.save(payload, out_path)
    print(f"\nSaved {len(indices)} samples to {out_path}")
    print(f"File size: {os.path.getsize(out_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
