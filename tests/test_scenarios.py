import numpy as np

from clearrisk.market import (
    extreme_left_tail,
    simulate_correlated_assets,
    simulate_gaussian_paths,
    simulate_jump_diffusion_paths,
    simulate_student_t_paths,
)
from clearrisk.scenarios import generate_scenario_set, laptop_friendly_defaults


def test_same_seed_gives_same_output() -> None:
    a = simulate_gaussian_paths(
        n_paths=400,
        horizon_days=30,
        drift=0.03,
        volatility=0.20,
        seed=123,
    )
    b = simulate_gaussian_paths(
        n_paths=400,
        horizon_days=30,
        drift=0.03,
        volatility=0.20,
        seed=123,
    )
    assert np.array_equal(a, b)


def test_student_t_has_more_extreme_losses_than_gaussian() -> None:
    gaussian = simulate_gaussian_paths(
        n_paths=3000,
        horizon_days=30,
        drift=0.02,
        volatility=0.25,
        seed=7,
    )
    fat_tail = simulate_student_t_paths(
        n_paths=3000,
        horizon_days=30,
        drift=0.02,
        volatility=0.25,
        df=4.0,
        seed=7,
    )
    gaussian_tail = extreme_left_tail(gaussian, quantile=0.001)
    fat_tail_extreme = extreme_left_tail(fat_tail, quantile=0.001)
    assert fat_tail_extreme < gaussian_tail


def test_jump_diffusion_creates_occasional_large_jumps() -> None:
    baseline = simulate_gaussian_paths(
        n_paths=2000,
        horizon_days=40,
        drift=0.02,
        volatility=0.20,
        seed=42,
    )
    jumpy = simulate_jump_diffusion_paths(
        n_paths=2000,
        horizon_days=40,
        drift=0.02,
        volatility=0.20,
        jump_probability=0.03,
        jump_mean=-0.12,
        jump_std=0.03,
        seed=42,
    )
    jump_threshold = -0.08
    baseline_jumps = int((baseline < jump_threshold).sum())
    jumpy_jumps = int((jumpy < jump_threshold).sum())
    assert jumpy_jumps > baseline_jumps
    assert jumpy_jumps > 0


def test_default_examples_laptop_friendly_and_scenario_set_complete() -> None:
    defaults = laptop_friendly_defaults()
    assert defaults["quickstart_n_paths"] <= 500
    assert defaults["standard_n_paths"] <= 1000
    assert defaults["dashboard_n_paths"] <= 500
    assert defaults["stress_lab_n_paths"] <= 10000
    assert defaults["default_horizon_days"] == 252

    scenarios = generate_scenario_set()
    labels = {s.stress_label for s in scenarios}
    assert "baseline" in labels
    assert "fat_tail" in labels
    assert "jump_diffusion" in labels
    assert "high_vol_stress" in labels


def test_correlated_multi_asset_generation_shape() -> None:
    returns = simulate_correlated_assets(
        n_paths=100,
        horizon_days=20,
        drifts=np.array([0.03, 0.02, 0.01]),
        volatilities=np.array([0.2, 0.25, 0.3]),
        correlation_matrix=np.array(
            [
                [1.0, 0.4, 0.2],
                [0.4, 1.0, 0.35],
                [0.2, 0.35, 1.0],
            ]
        ),
        seed=11,
    )
    assert returns.shape == (100, 20, 3)

