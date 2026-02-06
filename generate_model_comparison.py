"""
Generate model comparison data: Monte Carlo vs Hybrid XGBoost+Poisson
"""

import json
from pathlib import Path
from analysis.player_props_model import generate_player_props as monte_carlo_props
from analysis.hybrid_model import generate_hybrid_props


# Typical lines for comparison
COMPARISON_LINES = {
    'QB': {
        'passing_yards': 249.5,
        'passing_tds': 1.5,
        'interceptions': 0.5,
        'rushing_yards': 24.5
    },
    'RB': {
        'rushing_yards': 64.5,
        'rushing_tds': 0.5,
        'receptions': 3.5,
        'receiving_yards': 24.5
    },
    'WR': {
        'receptions': 5.5,
        'receiving_yards': 64.5,
        'receiving_tds': 0.5
    },
    'TE': {
        'receptions': 4.5,
        'receiving_yards': 49.5,
        'receiving_tds': 0.5
    }
}


def compare_models_for_player(player_name: str, position: str):
    """Compare Monte Carlo and Hybrid models for a player"""

    # Get predictions from both models
    mc_props = monte_carlo_props(player_name, position)
    hybrid_props = generate_hybrid_props(player_name, position)

    comparison = {
        'player_name': player_name,
        'position': position,
        'stats': {}
    }

    # Get typical lines for this position
    typical_lines = COMPARISON_LINES.get(position, {})

    # Compare each stat
    for stat_key in set(list(mc_props.keys()) + list(hybrid_props.keys())):
        stat_comparison = {}

        # Monte Carlo results
        if stat_key in mc_props:
            mc = mc_props[stat_key]
            line = typical_lines.get(stat_key, mc.line)

            stat_comparison['monte_carlo'] = {
                'prediction': mc.mean,
                'median': mc.median,
                'std_dev': mc.std_dev,
                'confidence_80': list(mc.confidence_80),
                'over_prob': mc.over_prob,
                'under_prob': mc.under_prob,
                'line': line
            }

        # Hybrid model results
        if stat_key in hybrid_props:
            hybrid = hybrid_props[stat_key]
            line = typical_lines.get(stat_key, hybrid.prediction)

            # Calculate over/under for same line as MC
            if stat_key in mc_props:
                line = typical_lines.get(stat_key, mc_props[stat_key].line)

            stat_comparison['hybrid'] = {
                'prediction': hybrid.prediction,
                'confidence_80': list(hybrid.confidence_interval),
                'model_type': hybrid.model_type,
                'over_prob': hybrid.over_prob,
                'under_prob': hybrid.under_prob,
                'features': hybrid.features_used,
                'line': line
            }

        # Calculate difference
        if 'monte_carlo' in stat_comparison and 'hybrid' in stat_comparison:
            mc_pred = stat_comparison['monte_carlo']['prediction']
            hybrid_pred = stat_comparison['hybrid']['prediction']

            stat_comparison['difference'] = {
                'prediction_diff': hybrid_pred - mc_pred,
                'prediction_diff_pct': ((hybrid_pred - mc_pred) / mc_pred * 100) if mc_pred > 0 else 0,
                'over_prob_diff': stat_comparison['hybrid']['over_prob'] - stat_comparison['monte_carlo']['over_prob']
            }

        if stat_comparison:
            comparison['stats'][stat_key] = stat_comparison

    return comparison


def generate_all_comparisons():
    """Generate comparisons for all players"""

    # Load player config
    config_path = Path("players_to_track.json")
    with open(config_path) as f:
        config = json.load(f)

    all_comparisons = {}

    print("🔬 Generating Model Comparisons...\n")

    for player in config['players']:
        name = player['name']
        position = player['position']

        if name.startswith("Player Name"):
            continue

        print(f"📊 Comparing models for {name} ({position})...")

        try:
            comparison = compare_models_for_player(name, position)
            all_comparisons[name] = comparison
        except Exception as e:
            print(f"   ⚠️  Error: {str(e)}")
            continue

    # Save to JSON
    output_path = Path("data/model_comparison.json")
    with open(output_path, 'w') as f:
        json.dump(all_comparisons, f, indent=2)

    print(f"\n✅ Generated comparisons for {len(all_comparisons)} players")
    print(f"📁 Saved to {output_path}")

    return all_comparisons


def print_summary(comparisons):
    """Print summary of model differences"""
    print("\n📈 MODEL COMPARISON SUMMARY\n")
    print("=" * 80)

    for player_name, data in comparisons.items():
        print(f"\n{player_name} ({data['position']}):")

        for stat_key, stat_data in data['stats'].items():
            if 'difference' in stat_data:
                diff = stat_data['difference']
                stat_name = stat_key.replace('_', ' ').title()

                mc_pred = stat_data['monte_carlo']['prediction']
                hy_pred = stat_data['hybrid']['prediction']
                model_type = stat_data['hybrid']['model_type']

                print(f"  {stat_name} ({model_type.upper()}):")
                print(f"    Monte Carlo: {mc_pred:.1f}")
                print(f"    Hybrid:      {hy_pred:.1f} ({diff['prediction_diff']:+.1f}, {diff['prediction_diff_pct']:+.1f}%)")

                if abs(diff['over_prob_diff']) >= 5:
                    print(f"    Over Prob Diff: {diff['over_prob_diff']:+.1f}% {'✨ SIGNIFICANT' if abs(diff['over_prob_diff']) >= 10 else ''}")


if __name__ == "__main__":
    comparisons = generate_all_comparisons()
    print_summary(comparisons)
