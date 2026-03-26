"""
N-BEATS forecaster for SmartGrowth AI.

N-BEATS (Neural Basis Expansion Analysis for Interpretable Time Series)
is a pure DL forecasting architecture from Element AI / ServiceNow Research
(Oreshkin et al., 2020). It uses no recurrence or convolution — only
stacked fully-connected blocks with basis expansion.

Two variants available:
  - Generic   : learned basis, highest accuracy, less interpretable
  - Interpretable : trend + seasonality basis, slightly lower accuracy but
                    decomposes the forecast into explainable components

We use the `neuralforecast` library (Nixtla) which provides a clean, fast
N-BEATS implementation on PyTorch.  Falls back to a lightweight manual
implementation if neuralforecast is unavailable.

Architecture reference:
    https://arxiv.org/abs/1905.10437
"""

from __future__ import annotations

import logging
import pickle
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
_NBEATS_INPUT_SIZE_MULTIPLIER = 5   # input_size = horizon * multiplier
_NBEATS_MAX_STEPS = 500
_NBEATS_LEARNING_RATE = 1e-3


class NBEATSForecaster:
    """
    N-BEATS forecaster.

    Primary backend: neuralforecast (Nixtla) — GPU-optional, fast.
    Fallback: manual N-BEATS in NumPy (CPU, slower but dependency-free).

    Usage:
        nf = NBEATSForecaster(horizon=30, interpretable=True)
        nf.fit(train_df)          # df must have 'ds' (datetime) and 'y' (float)
        preds = nf.predict()      # returns DataFrame: ds, yhat, yhat_lower, yhat_upper
    """

    def __init__(
        self,
        horizon: int = 30,
        interpretable: bool = True,
        input_size_multiplier: int = _NBEATS_INPUT_SIZE_MULTIPLIER,
        max_steps: int = _NBEATS_MAX_STEPS,
        learning_rate: float = _NBEATS_LEARNING_RATE,
        val_check_steps: int = 50,
        random_seed: int = 42,
    ):
        self.horizon = horizon
        self.interpretable = interpretable
        self.input_size = horizon * input_size_multiplier
        self.max_steps = max_steps
        self.learning_rate = learning_rate
        self.val_check_steps = val_check_steps
        self.random_seed = random_seed

        self.model = None
        self.backend: str = "none"
        self.train_df: Optional[pd.DataFrame] = None
        self.is_fitted: bool = False
        self._fallback_model: Optional["_NBeatsNumpy"] = None

    # ── Backend detection ─────────────────────────────────────────────────────

    def _get_backend(self) -> str:
        try:
            import neuralforecast  # noqa: F401
            return "neuralforecast"
        except ImportError:
            pass
        return "numpy_fallback"

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "NBEATSForecaster":
        """
        Train N-BEATS on df with columns [ds, y].
        """
        self.train_df = df[["ds", "y"]].copy()
        backend = self._get_backend()
        self.backend = backend

        if backend == "neuralforecast":
            self._fit_neuralforecast(df)
        else:
            logger.warning(
                "neuralforecast not installed — using lightweight numpy N-BEATS fallback.\n"
                "Install with: pip install neuralforecast"
            )
            self._fit_numpy_fallback(df)

        self.is_fitted = True
        logger.info(f"N-BEATS fitting complete (backend={self.backend})")
        return self

    def _fit_neuralforecast(self, df: pd.DataFrame) -> None:
        from neuralforecast import NeuralForecast
        from neuralforecast.models import NBEATS, NBEATSx

        # neuralforecast expects: unique_id, ds, y
        nf_df = df[["ds", "y"]].copy()
        nf_df["unique_id"] = "demand"

        ModelClass = NBEATS  # interpretable variant uses same class, different stack_types
        if self.interpretable:
            model = ModelClass(
                h=self.horizon,
                input_size=self.input_size,
                stack_types=["trend", "seasonality"],
                n_blocks=[3, 3],
                mlp_units=[[256, 256]] * 6,
                n_harmonics=2,
                n_polynomials=2,
                learning_rate=self.learning_rate,
                max_steps=self.max_steps,
                val_check_steps=self.val_check_steps,
                random_seed=self.random_seed,
                enable_progress_bar=True,
            )
        else:
            model = ModelClass(
                h=self.horizon,
                input_size=self.input_size,
                stack_types=["generic"],
                n_blocks=[3],
                mlp_units=[[512, 512]] * 3,
                learning_rate=self.learning_rate,
                max_steps=self.max_steps,
                val_check_steps=self.val_check_steps,
                random_seed=self.random_seed,
                enable_progress_bar=True,
            )

        self.model = NeuralForecast(models=[model], freq="D")
        self.model.fit(df=nf_df)

    def _fit_numpy_fallback(self, df: pd.DataFrame) -> None:
        self._fallback_model = _NBeatsNumpy(
            horizon=self.horizon,
            lookback=self.input_size,
            n_stacks=3,
            n_blocks=3,
            n_units=128,
            n_epochs=200,
        )
        self._fallback_model.fit(df["y"].values)

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self) -> pd.DataFrame:
        """
        Forecast `self.horizon` days beyond training data.

        Returns DataFrame: ds, yhat, yhat_lower, yhat_upper, model
        """
        if not self.is_fitted:
            raise RuntimeError("Call .fit() before .predict()")

        if self.train_df is None:
            raise RuntimeError("train_df is None — cannot generate future dates.")

        future_dates = pd.date_range(
            start=self.train_df["ds"].max() + pd.Timedelta(days=1),
            periods=self.horizon,
            freq="D",
        )

        if self.backend == "neuralforecast":
            yhat = self._predict_neuralforecast()
        else:
            yhat = self._fallback_model.predict()

        yhat = np.clip(yhat, 0, None)

        # Simple empirical confidence intervals: ±1.645σ from residual std
        residual_std = self._estimate_residual_std()
        margin = 1.645 * residual_std

        return pd.DataFrame({
            "ds":          future_dates,
            "yhat":        yhat.round(2),
            "yhat_lower":  np.clip(yhat - margin, 0, None).round(2),
            "yhat_upper":  (yhat + margin).round(2),
            "model":       "N-BEATS",
        })

    def _predict_neuralforecast(self) -> np.ndarray:
        nf_df = self.train_df.copy()
        nf_df["unique_id"] = "demand"
        result = self.model.predict(df=nf_df)
        # column name is model class name e.g. "NBEATS"
        val_col = [c for c in result.columns if c not in ["unique_id", "ds"]][0]
        return result[val_col].values

    def _estimate_residual_std(self) -> float:
        """Estimate forecast uncertainty from training data variability."""
        if self.train_df is not None and len(self.train_df) > 30:
            return self.train_df["y"].tail(60).std() * 0.5
        return 50.0  # fallback

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # neuralforecast model must be saved separately
        if self.backend == "neuralforecast":
            nf_path = str(Path(path).with_suffix("")) + "_nf_checkpoints"
            self.model.save(path=nf_path, model_index=None, overwrite=True, save_dataset=True)
            # Save wrapper metadata only
            meta = {
                "horizon": self.horizon,
                "interpretable": self.interpretable,
                "input_size": self.input_size,
                "max_steps": self.max_steps,
                "learning_rate": self.learning_rate,
                "random_seed": self.random_seed,
                "backend": self.backend,
                "nf_path": nf_path,
                "train_end_date": str(self.train_df["ds"].max()),
            }
            with open(path, "wb") as f:
                pickle.dump({"meta": meta, "train_df": self.train_df}, f)
        else:
            with open(path, "wb") as f:
                pickle.dump(self, f)
        logger.info(f"N-BEATS saved → {path}")

    @classmethod
    def load(cls, path: str) -> "NBEATSForecaster":
        with open(path, "rb") as f:
            data = pickle.load(f)

        if isinstance(data, dict) and "meta" in data:
            # neuralforecast path
            from neuralforecast import NeuralForecast
            meta = data["meta"]
            obj = cls(
                horizon=meta["horizon"],
                interpretable=meta["interpretable"],
                max_steps=meta["max_steps"],
            )
            obj.train_df = data["train_df"]
            obj.backend = "neuralforecast"
            obj.model = NeuralForecast.load(path=meta["nf_path"])
            obj.is_fitted = True
        else:
            obj = data

        logger.info(f"N-BEATS loaded ← {path}")
        return obj

    # ── Evaluation ────────────────────────────────────────────────────────────

    @staticmethod
    def evaluate(actual: np.ndarray, predicted: np.ndarray) -> dict:
        actual    = np.array(actual)
        predicted = np.array(predicted)
        mae  = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100
        return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "MAPE": round(mape, 3)}


# ── Lightweight numpy N-BEATS fallback ────────────────────────────────────────

class _NBeatsNumpy:
    """
    Minimal N-BEATS implementation in pure NumPy.

    Implements the core double-residual stacking idea:
      - Each block receives a backcast input and produces (backcast, forecast)
      - Backcast is subtracted from input (residual) for the next block
      - Forecasts are summed across all blocks

    This is NOT the full paper implementation — it omits basis expansion for
    simplicity.  Use only when neuralforecast is unavailable.
    """

    def __init__(
        self,
        horizon: int = 30,
        lookback: int = 150,
        n_stacks: int = 3,
        n_blocks: int = 3,
        n_units: int = 128,
        n_epochs: int = 200,
        learning_rate: float = 1e-3,
    ):
        self.horizon = horizon
        self.lookback = lookback
        self.n_stacks = n_stacks
        self.n_blocks = n_blocks
        self.n_units = n_units
        self.n_epochs = n_epochs
        self.learning_rate = learning_rate

        self._weights: list = []
        self._series: Optional[np.ndarray] = None
        self._scaler_mean: float = 0.0
        self._scaler_std: float = 1.0

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _linear(self, x: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
        return x @ W + b

    def _init_block_weights(self, in_dim: int) -> dict:
        rng = np.random.default_rng(42)
        scale = np.sqrt(2.0 / in_dim)
        return {
            "W1": rng.normal(0, scale, (in_dim, self.n_units)),
            "b1": np.zeros(self.n_units),
            "W2": rng.normal(0, scale, (self.n_units, self.n_units)),
            "b2": np.zeros(self.n_units),
            "Wf": rng.normal(0, 0.01, (self.n_units, self.horizon)),
            "bf": np.zeros(self.horizon),
            "Wb": rng.normal(0, 0.01, (self.n_units, self.lookback)),
            "bb": np.zeros(self.lookback),
        }

    def _forward_block(self, x: np.ndarray, w: dict):
        h = self._relu(self._linear(x, w["W1"], w["b1"]))
        h = self._relu(self._linear(h, w["W2"], w["b2"]))
        forecast  = self._linear(h, w["Wf"], w["bf"])
        backcast  = self._linear(h, w["Wb"], w["bb"])
        return backcast, forecast

    def fit(self, series: np.ndarray) -> "_NBeatsNumpy":
        self._series = series.astype(float)
        self._scaler_mean = series.mean()
        self._scaler_std  = max(series.std(), 1e-8)
        norm = (series - self._scaler_mean) / self._scaler_std

        # Build windows
        X, Y = [], []
        for i in range(len(norm) - self.lookback - self.horizon + 1):
            X.append(norm[i : i + self.lookback])
            Y.append(norm[i + self.lookback : i + self.lookback + self.horizon])
        X, Y = np.array(X), np.array(Y)

        total_blocks = self.n_stacks * self.n_blocks
        self._weights = [self._init_block_weights(self.lookback) for _ in range(total_blocks)]

        # Simple SGD with momentum (no autograd — plain numpy)
        lr = self.learning_rate
        momentum = {k: {p: np.zeros_like(v) for p, v in w.items()} for k, w in enumerate(self._weights)}
        mu = 0.9
        eps = 1e-8

        n_samples = len(X)
        batch_size = min(32, n_samples)

        rng = np.random.default_rng(42)
        for epoch in range(self.n_epochs):
            idx = rng.permutation(n_samples)
            epoch_loss = 0.0
            for start in range(0, n_samples, batch_size):
                batch_idx = idx[start:start + batch_size]
                xb = X[batch_idx]   # (B, lookback)
                yb = Y[batch_idx]   # (B, horizon)

                # Forward pass accumulating forecasts
                total_forecast = np.zeros_like(yb)
                residual = xb.copy()
                block_inputs = []
                block_outputs = []

                for bi, w in enumerate(self._weights):
                    bc, fc = self._forward_block(residual, w)
                    block_inputs.append(residual.copy())
                    block_outputs.append((bc, fc))
                    residual = residual - bc
                    total_forecast = total_forecast + fc

                loss = np.mean((total_forecast - yb) ** 2)
                epoch_loss += loss

                # Backward pass (simplified gradient via chain rule)
                grad_forecast = 2 * (total_forecast - yb) / len(yb)  # (B, horizon)

                for bi in range(len(self._weights) - 1, -1, -1):
                    w = self._weights[bi]
                    xi = block_inputs[bi]
                    bc, fc = block_outputs[bi]

                    # Gradient w.r.t. Wf, bf
                    h2 = self._relu(self._linear(
                        self._relu(self._linear(xi, w["W1"], w["b1"])),
                        w["W2"], w["b2"]
                    ))
                    gWf = h2.T @ grad_forecast / len(yb)
                    gbf = grad_forecast.mean(axis=0)

                    for p, g in [("Wf", gWf), ("bf", gbf)]:
                        momentum[bi][p] = mu * momentum[bi][p] + g
                        self._weights[bi][p] -= lr * momentum[bi][p]

            if epoch % 50 == 0:
                logger.debug(f"N-BEATS epoch {epoch:4d}  loss={epoch_loss:.4f}")

        return self

    def predict(self) -> np.ndarray:
        if self._series is None:
            raise RuntimeError("Call fit() first")
        norm = (self._series - self._scaler_mean) / self._scaler_std
        x = norm[-self.lookback:].reshape(1, -1)

        total_forecast = np.zeros((1, self.horizon))
        residual = x.copy()
        for w in self._weights:
            bc, fc = self._forward_block(residual, w)
            residual = residual - bc
            total_forecast = total_forecast + fc

        yhat_norm = total_forecast.flatten()
        return yhat_norm * self._scaler_std + self._scaler_mean


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_generator import generate_daily_demand, ForecastingConfig

    print("Generating data...")
    df = generate_daily_demand(ForecastingConfig(periods=400))
    train, test = df.iloc[:370], df.iloc[370:]

    print("Fitting N-BEATS (numpy fallback)...")
    nf = NBEATSForecaster(horizon=30, max_steps=100)
    nf.fit(train)
    preds = nf.predict()
    print(preds.head(10).to_string())

    metrics = NBEATSForecaster.evaluate(test["y"].values[:30], preds["yhat"].values)
    print(f"\nTest metrics: {metrics}")