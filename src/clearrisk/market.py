from __future__ import annotations

import math
from typing import Optional

import numpy as np

TRADING_DAYS = 252.0


def _validate_dimensions(n_paths: int, horizon_days: int) -> tuple[int, int]:
    paths = int(n_paths)
    horizon = int(horizon_days)
    if paths <= 0 or horizon <= 0:
        raise ValueError("n_paths and horizon_days must be positive integers")
    return paths, horizon


def simulate_gaussian_paths(
    n_paths: int,
    horizon_days: int,
    drift: float,
    volatility: float,
    seed: Optional[int] = None,
) -> np.ndarray:
    n_paths, horizon_days = _validate_dimensions(n_paths, horizon_days)
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    shocks = rng.normal(size=(n_paths, horizon_days))
    increments = (drift - 0.5 * volatility**2) * dt + volatility * math.sqrt(dt) * shocks
    return np.exp(increments) - 1.0


def simulate_student_t_paths(
    n_paths: int,
    horizon_days: int,
    drift: float,
    volatility: float,
    df: float = 5.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    n_paths, horizon_days = _validate_dimensions(n_paths, horizon_days)
    if df <= 2.0:
        raise ValueError("df must be > 2 for finite-variance Student-t returns")
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    raw = rng.standard_t(df=df, size=(n_paths, horizon_days))
    scaled = raw / math.sqrt(df / (df - 2.0))
    increments = (drift - 0.5 * volatility**2) * dt + volatility * math.sqrt(dt) * scaled
    return np.exp(increments) - 1.0


def simulate_jump_diffusion_paths(
    n_paths: int,
    horizon_days: int,
    drift: float,
    volatility: float,
    jump_probability: float,
    jump_mean: float = -0.08,
    jump_std: float = 0.05,
    seed: Optional[int] = None,
) -> np.ndarray:
    n_paths, horizon_days = _validate_dimensions(n_paths, horizon_days)
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS

    gaussian_shocks = rng.normal(size=(n_paths, horizon_days))
    base_increments = (drift - 0.5 * volatility**2) * dt + volatility * math.sqrt(dt) * gaussian_shocks

    jump_flags = rng.uniform(size=(n_paths, horizon_days)) < max(0.0, jump_probability)
    jump_sizes = rng.normal(loc=jump_mean, scale=max(0.0, jump_std), size=(n_paths, horizon_days))
    increments = base_increments + jump_flags * jump_sizes
    return np.exp(increments) - 1.0


def simulate_correlated_assets(
    n_paths: int,
    horizon_days: int,
    drifts: np.ndarray,
    volatilities: np.ndarray,
    correlation_matrix: np.ndarray,
    seed: Optional[int] = None,
) -> np.ndarray:
    n_paths, horizon_days = _validate_dimensions(n_paths, horizon_days)
    drifts = np.asarray(drifts, dtype=float)
    volatilities = np.asarray(volatilities, dtype=float)
    correlation_matrix = np.asarray(correlation_matrix, dtype=float)

    n_assets = len(drifts)
    if n_assets == 0:
        raise ValueError("drifts must contain at least one asset")
    if volatilities.shape != (n_assets,):
        raise ValueError("volatilities shape must match drifts shape")
    if correlation_matrix.shape != (n_assets, n_assets):
        raise ValueError("correlation_matrix must be square with dimension n_assets")

    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    chol = np.linalg.cholesky(correlation_matrix)
    z = rng.normal(size=(n_paths, horizon_days, n_assets))
    corr_z = z @ chol.T

    drift_term = (drifts - 0.5 * volatilities**2) * dt
    vol_term = volatilities * math.sqrt(dt)
    increments = drift_term + vol_term * corr_z
    return np.exp(increments) - 1.0


def extreme_left_tail(returns: np.ndarray, quantile: float = 0.001) -> float:
    q = min(max(float(quantile), 1e-6), 0.5)
    return float(np.quantile(np.asarray(returns), q))

