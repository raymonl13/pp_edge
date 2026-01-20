#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union, Any

import joblib
import numpy as np
import pandas as pd

# Default location for the v1 hit-probability model (shared across sports).
MODEL_PATH = Path("model_assets/model_v1.pkl")

ArrayLike = Union[np.ndarray, pd.DataFrame]


@dataclass
class LogisticHitModel:
    """
    Lightweight logistic regression model for hit-probability.

    This is intentionally minimal and numpy-only so we don't depend on
    heavyweight ML libraries. It expects features to be standardized
    using the stored mean_ and scale_ vectors.

    Attributes
    ----------
    feature_names : Sequence[str]
        Ordered list of feature column names used during training.
    coef_ : np.ndarray, shape (n_features,)
        Learned weights.
    intercept_ : float
        Scalar bias term.
    mean_ : np.ndarray, shape (n_features,)
        Per-feature means from the training data.
    scale_ : np.ndarray, shape (n_features,)
        Per-feature standard deviations from the training data.
        Any zero std is replaced with 1.0.
    """

    feature_names: Sequence[str]
    coef_: np.ndarray
    intercept_: float
    mean_: np.ndarray
    scale_: np.ndarray

    def _prepare_X(self, X: ArrayLike) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            X_mat = X.loc[:, list(self.feature_names)].to_numpy(dtype=float)
        else:
            X_mat = np.asarray(X, dtype=float)

        X_std = (X_mat - self.mean_) / self.scale_
        return X_std

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        z = np.clip(z, -50, 50)
        return 1.0 / (1.0 + np.exp(-z))

    def predict(self, X: ArrayLike) -> np.ndarray:
        """
        Return p_hit as probabilities in [0, 1].

        This matches the expectation of predict_hit_prob(), which uses
        the model's .predict output as hit probabilities.
        """
        X_std = self._prepare_X(X)
        z = X_std @ self.coef_ + float(self.intercept_)
        return self._sigmoid(z)


def load_model(model_path: Optional[Union[str, Path]] = None) -> Any:
    """
    Load the hit-probability model from disk.

    Parameters
    ----------
    model_path : Optional[str or Path]
        If provided, overrides the default MODEL_PATH.

    Returns
    -------
    Any
        A model object with a .predict(X) method that returns probabilities.
        This can be LogisticHitModel or any existing scikit-learn model.
    """
    mp = Path(model_path) if model_path is not None else MODEL_PATH
    return joblib.load(mp)


def save_model(model: Any, model_path: Optional[Union[str, Path]] = None) -> None:
    """
    Persist model to disk using joblib.
    """
    mp = Path(model_path) if model_path is not None else MODEL_PATH
    mp.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, mp)


def train_logistic_model(
    df: pd.DataFrame,
    feature_names: Sequence[str],
    target_col: str,
    num_iter: int = 2000,
    learning_rate: float = 0.01,
    l2_reg: float = 0.0,
) -> LogisticHitModel:
    """
    Train a simple logistic regression model using gradient descent.

    Parameters
    ----------
    df : pandas.DataFrame
        Training data containing feature columns and the binary target column.
    feature_names : sequence of str
        Names of feature columns to use.
    target_col : str
        Name of the binary target column (1 = hit, 0 = miss).
    num_iter : int, default 2000
        Number of gradient descent iterations.
    learning_rate : float, default 0.01
        Step size for gradient descent.
    l2_reg : float, default 0.0
        L2 regularization strength.

    Returns
    -------
    LogisticHitModel
        Trained model ready to be saved with save_model().
    """
    if not feature_names:
        raise ValueError("feature_names must be a non-empty sequence")

    X = df[list(feature_names)].to_numpy(dtype=float)
    y = df[target_col].to_numpy(dtype=float)

    if X.ndim != 2:
        raise ValueError(f"Expected 2D feature matrix, got shape {X.shape!r}")
    if y.ndim != 1:
        raise ValueError(f"Expected 1D target vector, got shape {y.shape!r}")
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"Mismatched X/y rows: {X.shape[0]} vs {y.shape[0]}")

    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0.0] = 1.0
    X_std = (X - mean) / std

    n_samples, n_features = X_std.shape
    w = np.zeros(n_features, dtype=float)
    b = 0.0

    for _ in range(num_iter):
        z = X_std @ w + b
        p = 1.0 / (1.0 + np.exp(-z))
        error = p - y
        grad_w = (X_std.T @ error) / n_samples + l2_reg * w
        grad_b = error.mean()
        w -= learning_rate * grad_w
        b -= learning_rate * grad_b

    return LogisticHitModel(
        feature_names=list(feature_names),
        coef_=w,
        intercept_=b,
        mean_=mean,
        scale_=std,
    )


def predict_hit_prob(
    df: pd.DataFrame,
    model_path: Optional[Union[str, Path]] = None,
) -> np.ndarray:
    """
    Convenience wrapper used by downstream scripts.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the feature columns expected by the model.
    model_path : Optional[str or Path]
        If provided, overrides the default MODEL_PATH.

    Returns
    -------
    np.ndarray
        Vector of hit probabilities for each row in df.
    """
    model = load_model(model_path)
    if not hasattr(model, "predict"):
        raise TypeError("Loaded model has no .predict method; cannot compute probabilities.")
    # For LogisticHitModel, passing df is fine; for scikit models, df is
    # typically acceptable as long as columns match training.
    probs = model.predict(df)
    return np.asarray(probs, dtype=float)
