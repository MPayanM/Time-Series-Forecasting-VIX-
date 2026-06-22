"""Plots for model evaluation results."""
import pandas as pd


def plot_forecast_vs_actual(actual: pd.Series, predicted: pd.Series) -> None:
    raise NotImplementedError


def plot_metrics_comparison(results: dict) -> None:
    """Bar chart comparing RMSE/MAE across models and horizons."""
    raise NotImplementedError
