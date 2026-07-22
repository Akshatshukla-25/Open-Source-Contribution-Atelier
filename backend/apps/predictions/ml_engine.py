import logging
import numpy as np

logger = logging.getLogger(__name__)


class PRReviewDelayPredictor:
    """
    ML Model engine for predicting PR review delays in hours.
    Fits XGBoost / Gradient Boosting regression model once at initialization,
    and supports online re-training on historical PR ground truth data.
    """

    def __init__(self):
        self.w_lines = 0.05
        self.w_files = 1.5
        self.w_workload = 8.0
        self.w_activity = -12.0
        self.base_delay = 12.0
        self.confidence_margin = 12.0
        self.model = None

        # Pre-fit model once on startup
        self._init_model()

    def _init_model(self):
        """
        Initializes and pre-fits the ensemble model once.
        """
        X_synthetic = np.array([
            [50, 2, 0, 1.0, 12],
            [200, 5, 2, 0.8, 24],
            [500, 15, 4, 0.5, 48],
            [1200, 30, 7, 0.2, 72],
        ])
        y_synthetic = np.array([12, 28, 64, 110])

        try:
            import xgboost as xgb
            self.model = xgb.XGBRegressor(n_estimators=50, max_depth=3, random_state=42)
            self.model.fit(X_synthetic, y_synthetic)
            logger.info("Initialized PR review delay predictor with XGBoost model.")
        except Exception:
            try:
                from sklearn.ensemble import GradientBoostingRegressor
                self.model = GradientBoostingRegressor(n_estimators=20, random_state=42)
                self.model.fit(X_synthetic, y_synthetic)
                logger.info("Initialized PR review delay predictor with GradientBoostingRegressor model.")
            except Exception as e:
                logger.warning("Could not initialize ML ensemble model: %s. Using mathematical fallback.", e)
                self.model = None

    def fit_model(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Re-trains the ML predictor on historical PR delay ground truth data.
        """
        if self.model is not None and len(X_train) > 0:
            self.model.fit(X_train, y_train)
            logger.info("Successfully re-trained PR review delay model on %d historical samples.", len(X_train))

    def extract_features(self, additions: int, deletions: int, changed_files: int,
                         current_workload: int, activity_score: float,
                         avg_response_time_hours: float) -> dict:
        total_lines = additions + deletions
        return {
            "total_lines": total_lines,
            "changed_files": changed_files,
            "current_workload": current_workload,
            "activity_score": activity_score,
            "avg_response_time_hours": avg_response_time_hours,
        }

    def predict(self, additions: int, deletions: int, changed_files: int,
                current_workload: int = 1, activity_score: float = 0.8,
                avg_response_time_hours: float = 24.0) -> dict:
        """
        Predicts review delay in hours using pre-fitted estimator or fallback formula.
        """
        features = self.extract_features(
            additions, deletions, changed_files,
            current_workload, activity_score, avg_response_time_hours
        )

        if self.model is not None:
            try:
                input_vec = np.array([[
                    features["total_lines"],
                    features["changed_files"],
                    features["current_workload"],
                    features["activity_score"],
                    features["avg_response_time_hours"]
                ]])
                predicted_delay = float(self.model.predict(input_vec)[0])
            except Exception as e:
                logger.warning("Model prediction error: %s. Using fallback calculation.", e)
                predicted_delay = self._fallback_calc(features)
        else:
            predicted_delay = self._fallback_calc(features)

        predicted_delay = max(4.0, round(predicted_delay, 1))
        risk_level = self.determine_risk_level(predicted_delay)

        return {
            "predicted_delay_hours": predicted_delay,
            "confidence_interval_hours": self.confidence_margin,
            "min_predicted_delay_hours": max(0.0, round(predicted_delay - self.confidence_margin, 1)),
            "max_predicted_delay_hours": round(predicted_delay + self.confidence_margin, 1),
            "risk_level": risk_level,
            "features": features,
        }

    def _fallback_calc(self, features: dict) -> float:
        lines_contrib = features["total_lines"] * self.w_lines
        files_contrib = features["changed_files"] * self.w_files
        workload_contrib = features["current_workload"] * self.w_workload
        activity_contrib = (1.0 - max(0.0, min(1.0, features["activity_score"]))) * abs(self.w_activity)
        response_contrib = features["avg_response_time_hours"] * 0.4
        return self.base_delay + lines_contrib + files_contrib + workload_contrib + activity_contrib + response_contrib

    def determine_risk_level(self, predicted_delay_hours: float) -> str:
        if predicted_delay_hours < 24.0:
            return "LOW"
        elif predicted_delay_hours < 48.0:
            return "MEDIUM"
        elif predicted_delay_hours < 72.0:
            return "HIGH"
        else:
            return "CRITICAL"


# Global singleton instance pre-fitted on startup
predictor = PRReviewDelayPredictor()
