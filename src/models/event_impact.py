"""Event → indicator impact association and effect-size estimation.

Improvements:
- Parses structured impact-link metadata (magnitude, lag_months, direction)
- Confidence- and magnitude-weighted effect sizes
- Temporal lag conversion (months → years) for forecasting hooks
- Optional decay assumptions by confidence
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.data_loader import load_enriched_data

OUT_DIR = Path(__file__).resolve().parents[2] / 'reports'
FIG_DIR = OUT_DIR / 'figures'
DATA_OUT = Path(__file__).resolve().parents[2] / 'data' / 'processed'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

# heuristic mapping for link indicators to canonical indicators
INDICATOR_MAP = {
    'digital': 'digital_payments',
    'usage': 'digital_payments',
    'mobile': 'mobile_subscribers',
    'subs': 'mobile_subscribers',
    'account': 'account_ownership',
    'ownership': 'account_ownership',
    'agent': 'agent_density',
    '4g': '4g_coverage',
}

CONFIDENCE_EFFECT = {
    'high': 0.06,
    'medium': 0.03,
    'low': 0.01,
}

MAGNITUDE_EFFECT = {
    'high': 0.06,
    'moderate': 0.035,
    'medium': 0.035,
    'low': 0.015,
}

DIRECTION_SIGN = {
    'increase': 1.0,
    'positive': 1.0,
    'up': 1.0,
    'decrease': -1.0,
    'negative': -1.0,
    'down': -1.0,
}


def _parse_kv_notes(text: str) -> dict:
    """Parse ``key=value`` pairs separated by `;` or `,` from notes fields."""
    meta = {}
    if not text or not isinstance(text, str):
        return meta
    for part in re.split(r'[;|]', text):
        part = part.strip()
        if '=' not in part:
            continue
        key, val = part.split('=', 1)
        meta[key.strip().lower()] = val.strip().lower()
    return meta


def parse_link_metadata(link_row) -> dict:
    """Extract target, effect size, lag, and decay from an impact_link row."""
    notes = str(link_row.get('notes') or '')
    evidence = str(link_row.get('evidence_basis') or '')
    kv = _parse_kv_notes(notes)
    kv.update({k: v for k, v in _parse_kv_notes(evidence).items() if k not in kv})

    confidence = str(link_row.get('confidence') or kv.get('confidence') or '').lower()
    magnitude = str(kv.get('impact_magnitude') or kv.get('magnitude') or '').lower()
    direction = str(kv.get('impact_direction') or kv.get('direction') or 'increase').lower()

    # Prefer explicit magnitude; blend with confidence when both present
    mag_effect = MAGNITUDE_EFFECT.get(magnitude)
    conf_effect = CONFIDENCE_EFFECT.get(confidence, 0.02)
    if mag_effect is not None:
        effect = 0.6 * mag_effect + 0.4 * conf_effect
    else:
        effect = conf_effect

    sign = DIRECTION_SIGN.get(direction, 1.0)
    effect = float(effect) * sign

    lag_months = kv.get('lag_months') or kv.get('lag')
    try:
        lag_months = int(float(lag_months)) if lag_months is not None else None
    except (TypeError, ValueError):
        lag_months = None

    # Also allow dedicated columns if present in wider schemas
    for col in ('lag_months', 'impact_magnitude', 'impact_direction'):
        if col in link_row.index and pd.notna(link_row.get(col)) and str(link_row.get(col)).strip():
            if col == 'lag_months' and lag_months is None:
                try:
                    lag_months = int(float(link_row.get(col)))
                except (TypeError, ValueError):
                    pass
            elif col == 'impact_magnitude' and magnitude == '':
                magnitude = str(link_row.get(col)).lower()
                if magnitude in MAGNITUDE_EFFECT:
                    effect = abs(effect) / max(abs(effect), 1e-12) * (
                        0.6 * MAGNITUDE_EFFECT[magnitude] + 0.4 * conf_effect
                    ) * sign
            elif col == 'impact_direction':
                direction = str(link_row.get(col)).lower()
                sign = DIRECTION_SIGN.get(direction, sign)
                effect = abs(effect) * sign

    lag_years = int(round(lag_months / 12.0)) if lag_months is not None else None
    # Higher confidence → slower decay (more persistent effect)
    decay = {'high': 0.92, 'medium': 0.88, 'low': 0.8}.get(confidence, 0.9)

    target = kv.get('target')
    if target in ('digital_payments', 'account_ownership', 'mobile_subscribers',
                  'agent_density', '4g_coverage'):
        pass
    else:
        target = infer_target_indicator(link_row)

    return {
        'target': target,
        'effect': effect,
        'confidence': confidence,
        'magnitude': magnitude,
        'direction': direction,
        'lag_months': lag_months,
        'lag_years': lag_years if lag_years is not None else 0,
        'decay': decay,
    }


def infer_target_indicator(link_row):
    # try indicator_code then indicator text
    code = str(link_row.get('indicator_code') or '')
    ind = str(link_row.get('indicator') or '')
    text = (code + ' ' + ind).lower()
    for k, v in INDICATOR_MAP.items():
        if k in text:
            return v
    notes = str(link_row.get('notes') or '') + ' ' + str(link_row.get('evidence_basis') or '')
    for k, v in INDICATOR_MAP.items():
        if k in notes.lower():
            return v
    return None


def match_event(parent_id, events_df):
    if pd.isna(parent_id):
        return None
    pid = str(parent_id).strip().lower()
    if not pid:
        return None

    name_col = events_df['source_name'].astype(str).str.lower().fillna('')
    m = events_df[name_col.str.contains(re.escape(pid), regex=True)]
    if not m.empty:
        return m.iloc[0]

    notes_col = events_df['notes'].astype(str).str.lower().fillna('')
    m = events_df[notes_col.str.contains(re.escape(pid), regex=True)]
    if not m.empty:
        return m.iloc[0]

    ind_col = events_df['indicator'].astype(str).str.lower().fillna('')
    m = events_df[ind_col.str.contains(re.escape(pid), regex=True)]
    if not m.empty:
        return m.iloc[0]

    for _, r in events_df.iterrows():
        blob = ' '.join([
            str(r.get('notes', '')),
            str(r.get('original_text', '')),
            str(r.get('indicator', '')),
            str(r.get('source_name', '')),
        ]).lower()
        if pid in blob:
            return r
    return None


def build_association_matrix(df):
    events = df[df['record_type'] == 'event'].copy()
    links = df[df['record_type'] == 'impact_link'].copy()
    # Drop empty placeholder link rows
    has_indicator = links['indicator'].notna() & (links['indicator'].astype(str).str.strip() != '')
    has_meta = links['notes'].astype(str).str.contains('impact_', na=False)
    links = links[has_indicator | has_meta]

    event_names = []
    target_indicators = set()
    records = []

    for _, link in links.iterrows():
        parent = link.get('parent_id')
        if pd.isna(parent) or str(parent).strip() == '':
            parent = link.get('category') or link.get('source_name')
        event = match_event(parent, events)
        if event is not None:
            event_label = event.get('indicator') or event.get('notes') or event.get('source_name') or 'event'
        else:
            event_label = str(parent) if parent is not None else 'unknown_event'

        meta = parse_link_metadata(link)
        target = meta['target']
        if target is None:
            indicator_field = str(link.get('indicator') or '')
            if 'digital' in indicator_field.lower():
                target = 'digital_payments'
            elif 'mobile' in indicator_field.lower() or 'subs' in indicator_field.lower():
                target = 'mobile_subscribers'
            elif 'account' in indicator_field.lower():
                target = 'account_ownership'
            else:
                target = 'other'

        target_indicators.add(target)
        records.append({
            'event': event_label,
            'indicator': target,
            'effect': meta['effect'],
            'confidence': meta['confidence'],
            'magnitude': meta['magnitude'],
            'direction': meta['direction'],
            'lag_months': meta['lag_months'],
            'lag_years': meta['lag_years'],
            'decay': meta['decay'],
            'parent_id': parent,
        })
        if event_label not in event_names:
            event_names.append(event_label)

    indicators = sorted(list(target_indicators)) if target_indicators else []
    matrix = pd.DataFrame(0.0, index=event_names, columns=indicators)
    lag_matrix = pd.DataFrame(np.nan, index=event_names, columns=indicators)

    for r in records:
        # If multiple links map to same cell, keep the larger absolute effect
        prev = matrix.loc[r['event'], r['indicator']]
        if abs(r['effect']) >= abs(prev):
            matrix.loc[r['event'], r['indicator']] = r['effect']
            lag_matrix.loc[r['event'], r['indicator']] = r['lag_months'] if r['lag_months'] is not None else np.nan

    return matrix, records, lag_matrix


def event_impulse_profile(effect, lag_months=0, horizon_years=3, decay=0.9):
    """Return year-by-year additive impulse given lag and decay."""
    lag_years = int(round((lag_months or 0) / 12.0))
    profile = []
    for y in range(horizon_years):
        if y < lag_years:
            profile.append(0.0)
        else:
            profile.append(float(effect) * (decay ** (y - lag_years)))
    return profile


def save_results(matrix, records=None, lag_matrix=None):
    out_csv = OUT_DIR / 'event_indicator_matrix.csv'
    matrix.to_csv(out_csv)

    if lag_matrix is not None and not lag_matrix.empty:
        lag_matrix.to_csv(OUT_DIR / 'event_indicator_lags.csv')
        lag_matrix.to_csv(DATA_OUT / 'event_indicator_lags.csv')

    if records is not None:
        rec_df = pd.DataFrame(records)
        rec_df.to_csv(DATA_OUT / 'event_impact_records.csv', index=False)
        rec_df.to_csv(OUT_DIR / 'event_impact_records.csv', index=False)

    plt.figure(figsize=(8, max(2, max(len(matrix), 1) * 0.5)))
    if matrix.size > 0:
        sns.heatmap(matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0)
    plt.title('Event → Indicator Association Matrix (effect sizes)')
    plt.tight_layout()
    out_png = FIG_DIR / 'event_indicator_matrix.png'
    plt.savefig(out_png)
    plt.close()

    # Also copy matrix into processed data for the dashboard
    matrix.to_csv(DATA_OUT / 'event_indicator_matrix.csv')
    return out_csv, out_png


def main():
    df = load_enriched_data()
    matrix, records, lag_matrix = build_association_matrix(df)
    out_csv, out_png = save_results(matrix, records=records, lag_matrix=lag_matrix)
    print('Saved matrix CSV:', out_csv)
    print('Saved matrix heatmap:', out_png)
    print('Records:', len(records))
    for r in records:
        print(f"  {r['event']} -> {r['indicator']}: effect={r['effect']:.4f}, "
              f"lag_months={r['lag_months']}, decay={r['decay']}")


if __name__ == '__main__':
    main()
