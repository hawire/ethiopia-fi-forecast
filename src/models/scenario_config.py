"""Scenario configuration for Ethiopia FI forecasts.

Combines growth-adjustment knobs (from early scenario design) with the
fuller growth/event/residual scales used by ``forecast_advanced``.
"""

from __future__ import annotations

# Additive growth-rate adjustments (fractional points per year) used by
# ``scenario_analysis.generate_scenario_forecast``.
SCENARIO_CONFIG = {
    'pessimistic': {
        'growth_adjustment': -0.02,
        'description': (
            'Slower financial inclusion growth due to infrastructure '
            'and adoption constraints.'
        ),
    },
    'base': {
        'growth_adjustment': 0.00,
        'description': 'Continuation of the historical trend.',
    },
    'optimistic': {
        'growth_adjustment': 0.02,
        'description': (
            'Faster growth supported by stronger digital financial service '
            'adoption and infrastructure expansion.'
        ),
    },
}

# Multiplicative scales applied to trend *change* and event boosts
# (preferred path used by ``forecast_advanced.forecast_access_usage``).
SCENARIO_PARAMS = {
    'pessimistic': {
        'growth_scale': 0.6,
        'event_scale': 0.5,
        'residual_scale': 1.3,
        'description': 'Slower trend growth and weaker event transmission',
    },
    'base': {
        'growth_scale': 1.0,
        'event_scale': 1.0,
        'residual_scale': 1.0,
        'description': 'Continuation of estimated trend plus calibrated events',
    },
    'optimistic': {
        'growth_scale': 1.4,
        'event_scale': 1.5,
        'residual_scale': 1.2,
        'description': 'Faster adoption and stronger event pass-through',
    },
}


def get_scenario_params(scenario: str = 'base') -> dict:
    """Return merged scenario parameters for a named scenario."""
    scales = dict(SCENARIO_PARAMS.get(scenario, SCENARIO_PARAMS['base']))
    adj = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG['base'])
    scales['growth_adjustment'] = adj.get('growth_adjustment', 0.0)
    if 'description' not in scales or not scales['description']:
        scales['description'] = adj.get('description', '')
    return scales
