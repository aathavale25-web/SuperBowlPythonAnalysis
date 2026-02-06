"""
Hybrid XGBoost + Poisson model for player prop predictions
Combines gradient boosting for yards with Poisson regression for counting stats
"""

import numpy as np
import duckdb
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available, using fallback linear model")

from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor, Ridge
from sklearn.preprocessing import StandardScaler


@dataclass
class HybridPrediction:
    """Prediction from hybrid model"""
    stat_name: str
    prediction: float
    confidence_interval: Tuple[float, float]  # 80% CI
    model_type: str  # "xgboost", "poisson", or "linear"
    over_prob: float
    under_prob: float
    features_used: List[str]


def load_player_games(player_name: str, season: int = 2025):
    """Load detailed game data for a player"""
    conn = duckdb.connect('data/superbowl.db')

    games = conn.execute("""
        SELECT
            week, game_type, game_result, opponent_abbr,
            passing_yards, passing_tds, interceptions,
            rushing_yards, rushing_tds,
            receptions, receiving_yards, receiving_tds
        FROM player_game_logs
        WHERE player_name = ? AND season = ?
        ORDER BY week
    """, [player_name, season]).fetchall()

    conn.close()
    return games


def engineer_features(games: List, recent_window: int = 5) -> np.ndarray:
    """
    Engineer features for ML model

    Features:
    - Recent form (last N games average)
    - Season average
    - Trend (recent vs early season)
    - Win/loss split performance
    - Consistency (std deviation)
    """
    if len(games) == 0:
        return np.array([])

    # For each game, create features based on data BEFORE that game
    features = []

    for i in range(len(games)):
        if i < 3:  # Need at least 3 games for features
            continue

        prior_games = games[:i]

        # Get recent games (last N before current)
        recent = prior_games[-recent_window:] if len(prior_games) >= recent_window else prior_games

        # Calculate various stats (example: passing yards at index 4)
        # This is a simplified version - in production you'd have stat-specific features
        game_data = [g[4:] for g in prior_games]  # All stat columns
        recent_data = [g[4:] for g in recent]

        if len(game_data) > 0:
            # Feature engineering for first stat (e.g., passing yards)
            stat_values = [g[0] for g in game_data]
            recent_values = [g[0] for g in recent_data]

            feat = [
                np.mean(recent_values),  # Recent average
                np.mean(stat_values),    # Season average
                np.std(stat_values),     # Consistency
                np.max(stat_values),     # Ceiling
                np.min(stat_values),     # Floor
                len(prior_games),        # Games played
            ]

            features.append(feat)

    return np.array(features) if features else np.array([])


def train_xgboost_model(historical_values: np.ndarray) -> XGBRegressor:
    """Train XGBoost model for yards prediction"""
    if not XGBOOST_AVAILABLE or len(historical_values) < 10:
        # Fallback to linear regression
        return None

    # Create simple features from historical data
    X = []
    y = []

    for i in range(5, len(historical_values)):
        # Features: last 5 games stats
        recent_5 = historical_values[i-5:i]
        features = [
            np.mean(recent_5),
            np.std(recent_5),
            np.max(recent_5),
            np.min(recent_5),
            historical_values[i-1],  # Last game
        ]
        X.append(features)
        y.append(historical_values[i])

    if len(X) < 5:
        return None

    X = np.array(X)
    y = np.array(y)

    model = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42
    )

    model.fit(X, y)
    return model


def predict_with_xgboost(model, historical_values: np.ndarray, n_simulations: int = 1000) -> np.ndarray:
    """Generate predictions using XGBoost with uncertainty"""
    if model is None or len(historical_values) < 5:
        # Fallback to simple average with noise
        mean = np.mean(historical_values[-5:])
        std = np.std(historical_values) * 1.1
        return np.random.normal(mean, std, n_simulations)

    # Create features for prediction
    recent_5 = historical_values[-5:]
    features = np.array([[
        np.mean(recent_5),
        np.std(recent_5),
        np.max(recent_5),
        np.min(recent_5),
        historical_values[-1],
    ]])

    # Get prediction
    prediction = model.predict(features)[0]

    # Estimate uncertainty from historical residuals
    X_train = []
    for i in range(5, len(historical_values)):
        recent = historical_values[i-5:i]
        X_train.append([
            np.mean(recent),
            np.std(recent),
            np.max(recent),
            np.min(recent),
            historical_values[i-1],
        ])

    y_train = historical_values[5:]
    predictions_train = model.predict(np.array(X_train))
    residuals = y_train - predictions_train
    residual_std = np.std(residuals) if len(residuals) > 0 else np.std(historical_values)

    # Generate predictions with uncertainty
    predictions = np.random.normal(prediction, residual_std * 1.1, n_simulations)
    return np.maximum(predictions, 0)  # No negative values


def predict_with_poisson(historical_values: np.ndarray, n_simulations: int = 1000) -> np.ndarray:
    """
    Predict counting stats using Poisson distribution
    Better for TDs, receptions, interceptions
    """
    # Weight recent games more
    if len(historical_values) >= 5:
        recent = historical_values[-5:]
        lambda_param = np.mean(recent) * 0.7 + np.mean(historical_values) * 0.3
    else:
        lambda_param = np.mean(historical_values)

    # Super Bowl bump (slightly higher variance)
    lambda_param = lambda_param * 1.05

    # Generate predictions
    predictions = poisson.rvs(lambda_param, size=n_simulations)
    return predictions.astype(float)


def hybrid_predict(stat_values: np.ndarray, stat_name: str, line: float = None) -> HybridPrediction:
    """
    Use appropriate model based on stat type
    - XGBoost for yards (continuous)
    - Poisson for counts (TDs, receptions, INTs)
    """
    if len(stat_values) == 0:
        return None

    # Determine model type based on stat
    is_count_stat = any(word in stat_name.lower() for word in ['td', 'touchdown', 'reception', 'interception'])

    if is_count_stat:
        # Use Poisson for counting stats
        predictions = predict_with_poisson(stat_values)
        model_type = "poisson"
        features = ["recent_games", "season_average", "poisson_lambda"]
    else:
        # Use XGBoost for yards
        model = train_xgboost_model(stat_values)
        predictions = predict_with_xgboost(model, stat_values)
        model_type = "xgboost" if model is not None else "linear"
        features = ["recent_form", "consistency", "ceiling", "floor", "trend"]

    # Calculate statistics
    mean = np.mean(predictions)
    median = np.median(predictions)
    ci_low = np.percentile(predictions, 10)
    ci_high = np.percentile(predictions, 90)

    # Determine line if not provided
    if line is None:
        line = median

    # Calculate probabilities
    over_prob = np.mean(predictions > line) * 100
    under_prob = 100 - over_prob

    return HybridPrediction(
        stat_name=stat_name,
        prediction=mean,
        confidence_interval=(ci_low, ci_high),
        model_type=model_type,
        over_prob=over_prob,
        under_prob=under_prob,
        features_used=features
    )


def generate_hybrid_props(player_name: str, position: str, season: int = 2025) -> Dict[str, HybridPrediction]:
    """Generate predictions using hybrid model"""
    games = load_player_games(player_name, season)

    if len(games) == 0:
        return {}

    props = {}

    # Extract stat values (indices from game tuple)
    stat_map = {
        'passing_yards': (4, 'Passing Yards'),
        'passing_tds': (5, 'Passing TDs'),
        'interceptions': (6, 'Interceptions'),
        'rushing_yards': (7, 'Rushing Yards'),
        'rushing_tds': (8, 'Rushing TDs'),
        'receptions': (9, 'Receptions'),
        'receiving_yards': (10, 'Receiving Yards'),
        'receiving_tds': (11, 'Receiving TDs'),
    }

    # Position-specific props
    if position == 'QB':
        stats_to_predict = ['passing_yards', 'passing_tds', 'interceptions', 'rushing_yards']
    elif position == 'RB':
        stats_to_predict = ['rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards']
    elif position in ['WR', 'TE']:
        stats_to_predict = ['receptions', 'receiving_yards', 'receiving_tds']
    else:
        stats_to_predict = []

    for stat_key in stats_to_predict:
        if stat_key in stat_map:
            idx, name = stat_map[stat_key]
            values = np.array([g[idx] for g in games if g[idx] is not None])

            if len(values) > 0:
                pred = hybrid_predict(values, name)
                if pred:
                    props[stat_key] = pred

    return props


if __name__ == "__main__":
    print("🤖 Hybrid XGBoost + Poisson Model\n")

    # Test on Drake Maye
    props = generate_hybrid_props("Drake Maye", "QB")

    print("Drake Maye (QB) - Hybrid Model Predictions:\n")
    for stat_key, pred in props.items():
        print(f"{pred.stat_name} ({pred.model_type.upper()}):")
        print(f"  Prediction: {pred.prediction:.1f}")
        print(f"  80% Range: {pred.confidence_interval[0]:.0f}-{pred.confidence_interval[1]:.0f}")
        print(f"  Over {pred.prediction:.1f}: {pred.over_prob:.1f}%")
        print(f"  Features: {', '.join(pred.features_used)}")
        print()
