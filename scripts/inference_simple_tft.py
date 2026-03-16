"""
Minimal self-contained inference demo for the Karman TFT forecasting model.
No dataset CSV required — uses synthetic sample data to demonstrate the pipeline.

Usage:
    python scripts/inference_simple_tft.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from omegaconf import OmegaConf
from tft_torch import tft
from karman.nn import weight_init

torch.set_default_dtype(torch.float32)

MODEL_PATH = os.path.join(os.path.dirname(__file__),
                          '..', 'models',
                          'ts_karman_model_tft_run_gpu_tft_w_omni_and_soho_wo_indices_and_proxies_w_10000_lag_100_resolution_valid_mape_14.936_params_1074865.torch')

# Model architecture parameters (must match training)
NUM_STATIC_NUMERIC = 8       # altitude, latitude, lon_sin/cos, doy_sin/cos, sid_sin/cos
NUM_HISTORICAL_NUMERIC = 25  # omni_indices + omni_magnetic_field + omni_solar_wind + soho + msise
NUM_FUTURE_NUMERIC = 1
NUM_HISTORICAL_STEPS = 100   # lag_minutes=10000 / resolution_minutes=100

# Density normalization (log10 space, from training data)
LOG_MIN = -13.99995231628418
LOG_MAX = -9.80734920501709


def unscale_density(scaled, log_min, log_max):
    """Convert normalized log-space prediction back to density in kg/m^3."""
    tmp = (log_max - log_min) * (scaled + 1) / 2 + log_min
    return torch.pow(10, tmp)


def main():
    # 1. Build model configuration
    data_props = {
        'num_historical_numeric': NUM_HISTORICAL_NUMERIC,
        'num_static_numeric': NUM_STATIC_NUMERIC,
        'num_future_numeric': NUM_FUTURE_NUMERIC,
    }
    configuration = {
        'model': {
            'dropout': 0.05,
            'state_size': 64,
            'output_quantiles': [0.5],
            'lstm_layers': 2,
            'attention_heads': 4,
        },
        'task_type': 'regression',
        'target_window_start': None,
        'data_props': data_props,
    }

    # 2. Load model
    model = tft.TemporalFusionTransformer(OmegaConf.create(configuration))
    model.apply(weight_init)
    model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu', weights_only=True))
    model.eval()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Loaded TFT model with {n_params:,} parameters")
    print(f"  Static features:     {NUM_STATIC_NUMERIC}")
    print(f"  Historical features: {NUM_HISTORICAL_NUMERIC} x {NUM_HISTORICAL_STEPS} steps")
    print(f"  Future features:     {NUM_FUTURE_NUMERIC}\n")

    # 3. Create synthetic demo inputs
    #    In a real application these would come from the KarmanDataset, which
    #    loads satellite telemetry (static features) and space weather time
    #    series (OMNI, SOHO, NRLMSISE-00).
    batch_size = 4
    torch.manual_seed(42)
    inputs = {
        'static_feats_numeric':   torch.randn(batch_size, NUM_STATIC_NUMERIC),
        'historical_ts_numeric':  torch.randn(batch_size, NUM_HISTORICAL_STEPS, NUM_HISTORICAL_NUMERIC),
        'future_ts_numeric':      torch.randn(batch_size, 1, NUM_FUTURE_NUMERIC),
    }

    # 4. Run inference
    with torch.no_grad():
        out = model(inputs)

    # predicted_quantiles shape: (batch_size, future_steps=1, num_quantiles=1)
    predicted_quantiles = out['predicted_quantiles']
    median_pred = predicted_quantiles[:, :, 0].squeeze()

    # Convert from normalized log-space to density in kg/m^3
    density_pred = unscale_density(median_pred, LOG_MIN, LOG_MAX)

    print(f"{'Sample':>6}  {'Raw output':>12}  {'Predicted [kg/m³]':>20}")
    print("-" * 44)
    for i in range(batch_size):
        print(f"{i:>6}  {median_pred[i].item():>12.6f}  {density_pred[i].item():>20.6e}")

    print("\nNote: predictions use synthetic random inputs and are not")
    print("physically meaningful. With real data from KarmanDataset,")
    print("this model achieves ~14.9% MAPE on the validation set.")


if __name__ == '__main__':
    main()
