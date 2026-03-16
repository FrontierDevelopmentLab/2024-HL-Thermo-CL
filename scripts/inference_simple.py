"""
Minimal self-contained inference demo for the Karman nowcasting model.
No dataset CSV required — uses bundled sample data.

Usage:
    python scripts/inference_simple.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import torch
from karman.nn import SimpleNetwork

torch.set_default_dtype(torch.float32)

MODEL_PATH = os.path.join(os.path.dirname(__file__),
                          '..', 'models',
                          'karman_nowcast_model_log_exp_residual_valid_mape_15.14_params_35585.torch')
SAMPLES_PATH = os.path.join(os.path.dirname(__file__), 'demo_samples.json')
HIDDEN_LAYER_DIM = 128
HIDDEN_LAYERS = 3


def scale_density(density, log_min, log_max):
    """Scale raw density to normalized log space [-1, 1]."""
    tmp = torch.log10(density)
    return 2.0 * (tmp - log_min) / (log_max - log_min) - 1.0


def unscale_density(scaled, log_min, log_max):
    """Convert normalized log-space prediction back to density in kg/m^3."""
    tmp = (log_max - log_min) * (scaled + 1) / 2 + log_min
    return torch.pow(10, tmp)


def main():
    # 1. Load sample data
    with open(SAMPLES_PATH) as f:
        data = json.load(f)

    log_min = data['normalization_dict']['log_exp_residual']['min']
    log_max = data['normalization_dict']['log_exp_residual']['max']
    feature_names = data['feature_names']
    samples = data['samples']

    # 2. Load model
    n_features = len(feature_names)
    model = SimpleNetwork(
        input_dim=n_features,
        act=torch.nn.LeakyReLU(negative_slope=0.01),
        hidden_layer_dims=[HIDDEN_LAYER_DIM] * HIDDEN_LAYERS,
        output_dim=1,
    )
    model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu', weights_only=True))
    model.eval()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Loaded model with {n_params} parameters")
    print(f"Input features ({n_features}): {feature_names}\n")

    # 3. Run inference
    print(f"{'Sample':>6}  {'Predicted [kg/m³]':>20}  {'Ground Truth [kg/m³]':>22}  {'MAPE [%]':>10}")
    print("-" * 65)

    mape_total = 0.0
    for i, s in enumerate(samples):
        features = torch.tensor(s['instantaneous_features']).unsqueeze(0)
        expo_atm = torch.tensor(s['exponential_atmosphere'])
        ground_truth = s['ground_truth']

        with torch.no_grad():
            out_nn = torch.tanh(model(features).squeeze())
            scaled_pred = scale_density(expo_atm, log_min, log_max) + out_nn
            density_pred = unscale_density(scaled_pred, log_min, log_max).item()

        mape = abs(density_pred - ground_truth) / ground_truth * 100
        mape_total += mape
        print(f"{i:>6}  {density_pred:>20.6e}  {ground_truth:>22.6e}  {mape:>10.2f}")

    print("-" * 65)
    print(f"Mean Absolute Percentage Error: {mape_total / len(samples):.2f}%")


if __name__ == '__main__':
    main()
