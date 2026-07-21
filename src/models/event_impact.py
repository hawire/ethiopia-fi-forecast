import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from src.data_loader import load_enriched_data

OUT_DIR = Path(__file__).resolve().parents[2] / 'reports'
FIG_DIR = OUT_DIR / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# heuristic mapping for link indicators to canonical indicators
INDICATOR_MAP = {
    'digital': 'digital_payments',
    'mobile': 'mobile_subscribers',
    'account': 'account_ownership',
    'agent': 'agent_density',
    '4g': '4g_coverage'
}

CONFIDENCE_EFFECT = {
    'high': 0.06,
    'medium': 0.03,
    'low': 0.01
}


def infer_target_indicator(link_row):
    # try indicator_code then indicator text
    code = str(link_row.get('indicator_code') or '')
    ind = str(link_row.get('indicator') or '')
    text = (code + ' ' + ind).lower()
    for k, v in INDICATOR_MAP.items():
        if k in text:
            return v
    # fallback: look for keywords in notes or evidence
    notes = str(link_row.get('notes') or '') + ' ' + str(link_row.get('evidence_basis') or '')
    for k, v in INDICATOR_MAP.items():
        if k in notes.lower():
            return v
    return None


def match_event(parent_id, events_df):
    if pd.isna(parent_id):
        return None
    pid = str(parent_id).strip().lower()
    # match by source_name
    m = events_df[events_df['source_name'].str.lower().fillna('').str.contains(pid)]
    if not m.empty:
        return m.iloc[0]
    # match by notes or original_text
    m = events_df[events_df['notes'].str.lower().fillna('').str.contains(pid)]
    if not m.empty:
        return m.iloc[0]
    # no exact match, try substring matching on event indicator/notes
    for _, r in events_df.iterrows():
        if pid in str(r.get('notes','')).lower() or pid in str(r.get('original_text','')).lower():
            return r
    return None


def build_association_matrix(df):
    events = df[df['record_type']=='event'].copy()
    links = df[df['record_type']=='impact_link'].copy()
    # prepare events index
    event_names = []
    target_indicators = set()
    records = []
    for _, link in links.iterrows():
        parent = link.get('parent_id')
        # if parent_id is empty, try parent stored in category or source_name column
        if pd.isna(parent) or str(parent).strip()=='':
            parent = link.get('category') or link.get('source_name')
        event = match_event(parent, events)
        event_label = None
        if event is not None:
            event_label = event.get('notes') or event.get('source_name') or 'event'
        else:
            # fallback to parent text
            event_label = str(parent) or 'unknown_event'
        target = infer_target_indicator(link)
        if target is None:
            # try to parse from 'indicator' field
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
        confidence = str(link.get('confidence') or '').lower()
        effect = CONFIDENCE_EFFECT.get(confidence, 0.02)
        # record
        records.append({'event': event_label, 'indicator': target, 'effect': effect, 'confidence': confidence})
        if event_label not in event_names:
            event_names.append(event_label)
    # build matrix
    indicators = sorted(list(target_indicators))
    matrix = pd.DataFrame(0.0, index=event_names, columns=indicators)
    for r in records:
        matrix.loc[r['event'], r['indicator']] = r['effect']
    return matrix, records


def save_results(matrix):
    out_csv = OUT_DIR / 'event_indicator_matrix.csv'
    matrix.to_csv(out_csv)
    plt.figure(figsize=(8, max(2, len(matrix)*0.5)))
    sns.heatmap(matrix, annot=True, fmt='.3f', cmap='coolwarm')
    plt.title('Event → Indicator Association Matrix (effect sizes)')
    plt.tight_layout()
    out_png = FIG_DIR / 'event_indicator_matrix.png'
    plt.savefig(out_png)
    return out_csv, out_png


def main():
    df = load_enriched_data()
    matrix, records = build_association_matrix(df)
    out_csv, out_png = save_results(matrix)
    print('Saved matrix CSV:', out_csv)
    print('Saved matrix heatmap:', out_png)

if __name__ == '__main__':
    main()
