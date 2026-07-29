"""Reproducibility and forecast integration tests."""

import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_enriched_data, observation_timeseries
from src.models import backtesting, event_impact, forecast_advanced, sensitivity


@pytest.fixture(scope='module')
def enriched():
    return load_enriched_data()


@pytest.fixture(scope='module')
def obs(enriched):
    return forecast_advanced.load_observations(enriched)


def test_enriched_data_loads(enriched):
    assert len(enriched) >= 10
    assert 'record_type' in enriched.columns
    assert set(enriched['record_type'].unique()) >= {'observation', 'event', 'impact_link'}


def test_account_ownership_series(enriched):
    ts = observation_timeseries(enriched, 'account_ownership')
    assert len(ts) >= 3
    assert ts['year'].is_monotonic_increasing


def test_forecast_reproducibility(obs, enriched):
    r1, y1, m1 = forecast_advanced.forecast_access_usage(obs, enriched_df=enriched, seed=42, n_samples=50)
    r2, y2, m2 = forecast_advanced.forecast_access_usage(obs, enriched_df=enriched, seed=42, n_samples=50)
    np.testing.assert_allclose(r1['access']['base']['mean'], r2['access']['base']['mean'])
    np.testing.assert_allclose(r1['usage']['optimistic']['lower'], r2['usage']['optimistic']['lower'])
    assert list(y1) == list(y2)
    assert m1['seed'] == m2['seed'] == 42


def test_forecast_seed_changes_ci(obs, enriched):
    r1, _, _ = forecast_advanced.forecast_access_usage(obs, enriched_df=enriched, seed=1, n_samples=80)
    r2, _, _ = forecast_advanced.forecast_access_usage(obs, enriched_df=enriched, seed=99, n_samples=80)
    # Means of the trend path should be near-identical; sample percentiles can differ
    assert not np.allclose(r1['access']['base']['lower'], r2['access']['base']['lower'])


def test_scenario_ordering(obs, enriched):
    results, _, _ = forecast_advanced.forecast_access_usage(obs, enriched_df=enriched, seed=42)
    for ind in ('access', 'usage'):
        pess = results[ind]['pessimistic']['mean'][-1]
        base = results[ind]['base']['mean'][-1]
        opt = results[ind]['optimistic']['mean'][-1]
        assert pess <= base <= opt


def test_event_impact_matrix(enriched):
    matrix, records, lag_matrix = event_impact.build_association_matrix(enriched)
    assert len(records) >= 2
    assert matrix.shape[0] >= 1
    assert 'digital_payments' in matrix.columns or 'account_ownership' in matrix.columns
    assert any(r.get('lag_months') is not None for r in records)


def test_backtesting_metrics(obs):
    detail, summary = backtesting.run_indicator_backtests(obs)
    assert not summary.empty
    access_exp = summary[(summary['indicator'] == 'access') & (summary['method'] == 'expanding_window')]
    assert len(access_exp) == 1
    assert access_exp.iloc[0]['status'] == 'ok'
    assert access_exp.iloc[0]['n'] >= 1
    assert np.isfinite(access_exp.iloc[0]['mae'])


def test_sensitivity_tornado(obs):
    sens = sensitivity.run_sensitivity_analysis(obs)
    tornado = sensitivity.tornado_summary(sens)
    assert not sens.empty
    assert set(tornado['parameter']) >= {'growth_scale', 'event_scale'}
    # Sensitivity should be reproducible
    sens2 = sensitivity.run_sensitivity_analysis(obs)
    pd.testing.assert_frame_equal(sens.reset_index(drop=True), sens2.reset_index(drop=True))


def test_legacy_scenario_scaling_api():
    fc = {'mean': np.array([10.0, 20.0]), 'lower': np.array([9.0, 19.0]), 'upper': np.array([11.0, 21.0])}
    scaled = forecast_advanced.scenario_scaling(fc, 'optimistic')
    np.testing.assert_allclose(scaled['mean'], np.array([13.0, 26.0]))


def test_scenario_config_and_analysis_integration():
    from src.models import forecast_validation, scenario_analysis, scenario_config

    assert 'base' in scenario_config.SCENARIO_CONFIG
    assert 'growth_scale' in scenario_config.get_scenario_params('optimistic')
    path = scenario_analysis.generate_scenario_forecast([50.0, 52.0, 54.0], 2.0, 0.02)
    assert len(path) == 3
    assert path[0] == pytest.approx(50.0)
    assert path[1] == pytest.approx(52.02)
    stats = forecast_validation.validate_series([10, 20], [11, 18])
    assert stats['n'] == 2
    assert np.isfinite(stats['mae'])
