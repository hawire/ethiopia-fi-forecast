import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'processed' / 'ethiopia_fi_unified_data_enriched.csv'
OUT_DIR = Path(__file__).resolve().parents[1] / 'reports'
FIG_DIR = OUT_DIR / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

from src.data_loader import load_enriched_data


def load_data(path=None):
    if path is None:
        return load_enriched_data()
    df = pd.read_csv(path)
    df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
    df['value_numeric'] = pd.to_numeric(df['value_numeric'], errors='coerce')
    return df


def plot_account_ownership(df):
    obs = df[(df['record_type']=='observation') & (df['indicator_code']=='account_ownership')]
    fig, ax = plt.subplots(figsize=(8,4))
    sns.lineplot(data=obs, x='observation_date', y='value_numeric', marker='o', ax=ax)
    ax.set_title('Account Ownership (Global Findex)')
    ax.set_ylabel('Percent of adults')
    ax.set_xlabel('Date')
    # overlay events
    events = df[df['record_type']=='event']
    for _, e in events.iterrows():
        if pd.notna(e['observation_date']):
            ax.axvline(e['observation_date'], color='gray', linestyle='--', alpha=0.6)
            ax.text(e['observation_date'], ax.get_ylim()[1]*0.95, str(e.get('indicator','')) or str(e.get('notes','')) , rotation=90, fontsize=8)
    fig.tight_layout()
    p = FIG_DIR / 'account_ownership.png'
    fig.savefig(p)
    return fig


def plot_infrastructure_trends(df):
    figs = []
    infra_codes = ['mobile_subscribers','4g_coverage','agent_density']
    for code in infra_codes:
        obs = df[(df['record_type']=='observation') & (df['indicator_code']==code)]
        if obs.empty:
            continue
        fig, ax = plt.subplots(figsize=(8,4))
        sns.lineplot(data=obs, x='observation_date', y='value_numeric', marker='o', ax=ax)
        ax.set_title(code.replace('_',' ').title())
        ax.set_ylabel('Value')
        ax.set_xlabel('Date')
        fig.tight_layout()
        p = FIG_DIR / f'{code}.png'
        fig.savefig(p)
        figs.append(fig)
    return figs


def plot_correlation_matrix(df):
    obs = df[df['record_type']=='observation'].copy()
    pivot = obs.pivot_table(index='observation_date', columns='indicator_code', values='value_numeric', aggfunc='mean')
    pivot = pivot.sort_index()
    # Keep contiguous window
    corr = pivot.corr()
    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='vlag', ax=ax)
    ax.set_title('Correlation Matrix (observed indicators)')
    fig.tight_layout()
    p = FIG_DIR / 'correlation_matrix.png'
    fig.savefig(p)
    return fig


def plot_event_timeline(df):
    events = df[df['record_type']=='event'].copy()
    events = events[pd.notna(events['observation_date'])]
    if events.empty:
        return None
    fig, ax = plt.subplots(figsize=(10,2))
    y = [1]*len(events)
    ax.scatter(events['observation_date'], y)
    for i, (_, e) in enumerate(events.iterrows()):
        ax.text(e['observation_date'], 1.02, e.get('notes', '')[:40], rotation=45, fontsize=8)
    ax.get_yaxis().set_visible(False)
    ax.set_title('Event Timeline')
    fig.tight_layout()
    p = FIG_DIR / 'event_timeline.png'
    fig.savefig(p)
    return fig


def generate_pdfs(figures):
    # Two interim PDFs: enrichment and EDA
    eda_pdf = OUT_DIR / 'interim_report_eda.pdf'
    enrichment_pdf = OUT_DIR / 'interim_report_enrichment.pdf'
    # For enrichment, include event timeline and agent/infrastructure figures
    with PdfPages(enrichment_pdf) as pdf:
        for fname in ['event_timeline.png','mobile_subscribers.png','4g_coverage.png','agent_density.png']:
            p = FIG_DIR / fname
            if p.exists():
                fig = plt.imread(p)
                plt.figure(figsize=(8,6))
                plt.imshow(fig)
                plt.axis('off')
                pdf.savefig()
                plt.close()
    # For EDA, include account ownership and correlation
    with PdfPages(eda_pdf) as pdf:
        for fname in ['account_ownership.png','correlation_matrix.png']:
            p = FIG_DIR / fname
            if p.exists():
                fig = plt.imread(p)
                plt.figure(figsize=(8,6))
                plt.imshow(fig)
                plt.axis('off')
                pdf.savefig()
                plt.close()
    return enrichment_pdf, eda_pdf


def main():
    df = load_data(DATA_PATH)
    figs = []
    f1 = plot_account_ownership(df)
    figs.append(f1)
    figs += plot_infrastructure_trends(df)
    f3 = plot_correlation_matrix(df)
    figs.append(f3)
    f4 = plot_event_timeline(df)
    if f4 is not None:
        figs.append(f4)
    enrichment_pdf, eda_pdf = generate_pdfs(figs)
    print('Generated PDFs:')
    print(enrichment_pdf)
    print(eda_pdf)

if __name__ == '__main__':
    main()
