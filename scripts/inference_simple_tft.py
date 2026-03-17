"""
Inference demo for the Karman TFT forecasting model.

Loads pre-extracted real sample data (from extract_sample_data.py) and runs
the model, comparing predictions against ground-truth density measurements.

The model weights can be loaded from a local file or streamed directly from
an S3 bucket (requires ``smart_open``; ``pip install smart_open[s3]``).

Usage:
    python scripts/inference_simple_tft.py                          # real data
    python scripts/inference_simple_tft.py --synthetic              # synthetic fallback
    python scripts/inference_simple_tft.py --sample_data path.pt    # custom samples
    python scripts/inference_simple_tft.py --model_path s3://...    # load model from S3
"""
import sys
import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import torch
from omegaconf import OmegaConf
from tft_torch import tft
from karman.nn import weight_init

torch.set_default_dtype(torch.float32)

MODEL_PATH_LOCAL = os.path.join(os.path.dirname(__file__),
                          '..', 'models',
                          'ts_karman_model_tft_run_gpu_tft_w_omni_and_soho_wo_indices_and_proxies_w_10000_lag_100_resolution_valid_mape_14.936_params_1074865.torch')
MODEL_PATH_S3 = 's3://nasa-radiant-data/helioai-datasets/hl-therm/models/ts_karman_model_tft_run_gpu_tft_w_omni_and_soho_wo_indices_and_proxies_w_10000_lag_100_resolution_valid_mape_14.936_params_1074865.torch'
SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__),
                                '..', 'data', 'sample_inputs_tft.pt')

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


def load_real_data(path):
    """Load pre-extracted sample data produced by extract_sample_data.py."""
    data = torch.load(path, map_location='cpu', weights_only=False)
    inputs = {
        'static_feats_numeric':  data['static_feats_numeric'],
        'historical_ts_numeric': data['historical_ts_numeric'],
        'future_ts_numeric':     data['future_ts_numeric'],
    }
    return inputs, data


def make_synthetic_data(batch_size=4):
    """Generate random synthetic inputs as a fallback demo."""
    torch.manual_seed(42)
    inputs = {
        'static_feats_numeric':  torch.randn(batch_size, NUM_STATIC_NUMERIC),
        'historical_ts_numeric': torch.randn(batch_size, NUM_HISTORICAL_STEPS, NUM_HISTORICAL_NUMERIC),
        'future_ts_numeric':     torch.randn(batch_size, 1, NUM_FUTURE_NUMERIC),
    }
    return inputs, None


def main():
    parser = argparse.ArgumentParser(description="TFT inference demo")
    parser.add_argument('--synthetic', action='store_true',
                        help='Use synthetic random inputs instead of real data')
    parser.add_argument('--sample_data', type=str, default=SAMPLE_DATA_PATH,
                        help='Path to the .pt file with extracted sample data')
    parser.add_argument('--model_path', type=str, default=None,
                        help='Path or S3 URI for model weights (default: local file, '
                             'falls back to S3 if local not found)')
    parser.add_argument('--remote', action='store_true',
                        help='Force loading model weights from S3 instead of local file')
    args = parser.parse_args()

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

    # 2. Load model weights (local or S3)
    model = tft.TemporalFusionTransformer(OmegaConf.create(configuration))
    model.apply(weight_init)

    if args.model_path is not None:
        model_source = args.model_path
    elif args.remote:
        model_source = MODEL_PATH_S3
    elif os.path.exists(MODEL_PATH_LOCAL):
        model_source = MODEL_PATH_LOCAL
    else:
        print(f"Local model not found at {MODEL_PATH_LOCAL}")
        print("Falling back to S3...\n")
        model_source = MODEL_PATH_S3

    if model_source.startswith('s3://'):
        import smart_open
        print(f"Streaming model from {model_source} ...")
        with smart_open.open(model_source, 'rb') as f:
            state_dict = torch.load(io.BytesIO(f.read()), map_location='cpu', weights_only=True)
    else:
        print(f"Loading model from {model_source} ...")
        state_dict = torch.load(model_source, map_location='cpu', weights_only=True)

    model.load_state_dict(state_dict)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Loaded TFT model with {n_params:,} parameters")
    print(f"  Static features:     {NUM_STATIC_NUMERIC}")
    print(f"  Historical features: {NUM_HISTORICAL_NUMERIC} x {NUM_HISTORICAL_STEPS} steps")
    print(f"  Future features:     {NUM_FUTURE_NUMERIC}\n")

    # 3. Load inputs
    use_synthetic = args.synthetic
    if not use_synthetic and not os.path.exists(args.sample_data):
        print(f"Sample data not found at {args.sample_data}")
        print("Falling back to synthetic inputs. Run extract_sample_data.py first "
              "to generate real samples.\n")
        use_synthetic = True

    if use_synthetic:
        print("Using SYNTHETIC random inputs (not physically meaningful)\n")
        inputs, metadata = make_synthetic_data()
    else:
        print(f"Using REAL sample data from {args.sample_data}\n")
        inputs, metadata = load_real_data(args.sample_data)

    batch_size = inputs['static_feats_numeric'].shape[0]

    # 4. Run inference
    with torch.no_grad():
        out = model(inputs)

    # predicted_quantiles shape: (batch_size, future_steps=1, num_quantiles=1)
    predicted_quantiles = out['predicted_quantiles']
    median_pred = predicted_quantiles[:, :, 0].squeeze()

    # Convert from normalized log-space to density in kg/m^3
    density_pred = unscale_density(median_pred, LOG_MIN, LOG_MAX)

    # 5. Display results
    if metadata is not None and 'ground_truth' in metadata:
        # Real data: compare against ground truth
        ground_truth = metadata['ground_truth']
        nrlmsise00 = metadata['nrlmsise00']
        dates = metadata.get('dates', [None] * batch_size)

        print(f"{'#':>3}  {'Date':>22}  {'Predicted [kg/m3]':>18}  {'Truth [kg/m3]':>18}  {'NRLMSISE [kg/m3]':>18}  {'NN err%':>8}  {'MSISE err%':>10}")
        print("-" * 108)
        nn_apes = []
        msise_apes = []
        for i in range(batch_size):
            pred_val = density_pred[i].item()
            true_val = ground_truth[i].item()
            msise_val = nrlmsise00[i].item()
            nn_ape = abs(pred_val - true_val) / abs(true_val) * 100
            msise_ape = abs(msise_val - true_val) / abs(true_val) * 100
            nn_apes.append(nn_ape)
            msise_apes.append(msise_ape)
            date_str = dates[i] if dates[i] else ""
            print(f"{i:>3}  {date_str:>22}  {pred_val:>18.6e}  {true_val:>18.6e}  {msise_val:>18.6e}  {nn_ape:>7.1f}%  {msise_ape:>9.1f}%")

        print("\nMean Absolute Percentage Error:")
        print(f"  TFT model:   {sum(nn_apes)/len(nn_apes):.1f}%")
        print(f"  NRLMSISE-00: {sum(msise_apes)/len(msise_apes):.1f}%")
    else:
        # Synthetic data: just show raw outputs
        print(f"{'Sample':>6}  {'Raw output':>12}  {'Predicted [kg/m3]':>20}")
        print("-" * 44)
        for i in range(batch_size):
            print(f"{i:>6}  {median_pred[i].item():>12.6f}  {density_pred[i].item():>20.6e}")
        print("\nNote: predictions use synthetic random inputs and are not")
        print("physically meaningful.")


if __name__ == '__main__':
    main()
