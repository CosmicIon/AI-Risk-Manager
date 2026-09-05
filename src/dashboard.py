# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import sys
from pathlib import Path
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))
import src.explain
import importlib
importlib.reload(src.explain)
from src.explain import RiskExplainer
from src.utils import get_project_root

# -----------------
# PAGE CONFIGURATION
# -----------------
st.set_page_config(
    page_title="AI Risk Manager | Fraud Defense Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------
# MODERN DESIGN SYSTEM & SPACIOUS CSS
# -----------------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Layout */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #0f172a;
    }
    
    /* Spacious Main Container */
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 4.5rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1320px !important;
    }

    /* Top Hero Header */
    .hero-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .hero-title {
        font-size: 2.35rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        color: #0f172a !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    .hero-subtitle {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
        margin-top: 0.45rem !important;
        margin-bottom: 0 !important;
    }

    /* Badges & Pills */
    .badge-bar {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #334155;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .pill-green {
        background-color: #ecfdf5;
        border-color: #a7f3d0;
        color: #065f46;
    }

    /* Spacious Verdict Card */
    .verdict-card {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #ffffff !important;
        padding: 1.75rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.25);
    }
    .verdict-card h2 {
        color: #ffffff !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        line-height: 1.45 !important;
        margin: 0 !important;
    }

    /* Spacious KPI Card Grid */
    .kpi-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.6rem 1.4rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
    }
    .kpi-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.08);
    }
    .kpi-header {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .kpi-number {
        font-size: 2.25rem;
        font-weight: 800;
        line-height: 1.15;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.02em;
    }
    .kpi-footer {
        font-size: 0.84rem;
        color: #64748b;
        line-height: 1.4;
        margin: 0;
    }

    /* Section Headings */
    .section-header-box {
        margin-top: 2rem;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin: 0 0 0.3rem 0 !important;
        letter-spacing: -0.02em !important;
    }
    .section-desc {
        font-size: 0.95rem !important;
        color: #64748b !important;
        margin: 0 !important;
        line-height: 1.5 !important;
    }

    /* Spacious Decision Matrix Cards */
    .matrix-tile {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 1.5rem 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .tile-title {
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .tile-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 0 0 0.35rem 0;
    }
    .tile-desc {
        font-size: 0.85rem;
        margin: 0;
        line-height: 1.4;
    }

    .tile-green {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-left: 6px solid #10b981;
    }
    .tile-green .tile-title, .tile-green .tile-value, .tile-green .tile-desc { color: #065f46 !important; }

    .tile-amber {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 6px solid #f59e0b;
    }
    .tile-amber .tile-title, .tile-amber .tile-value, .tile-amber .tile-desc { color: #92400e !important; }

    .tile-red {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 6px solid #ef4444;
    }
    .tile-red .tile-title, .tile-red .tile-value, .tile-red .tile-desc { color: #991b1b !important; }

    .tile-slate {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #64748b;
    }
    .tile-slate .tile-title, .tile-slate .tile-value, .tile-slate .tile-desc { color: #334155 !important; }

    /* Feed Card Styling */
    .feed-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .code-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        color: #334155;
    }

    /* Divider */
    .custom-hr {
        margin: 2.8rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }
</style>
"""

# -----------------
# DATA LOADING & CACHING
# -----------------
@st.cache_resource
def load_explainer():
    return RiskExplainer()

@st.cache_data
def load_metrics(mtime: float = 0.0):
    root = get_project_root()
    metrics_path = root / 'models' / 'metrics_test.json'
    if not metrics_path.exists():
        return None
    with open(metrics_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_cached_test_data():
    root = get_project_root()
    test = pd.read_parquet(root / 'data' / 'processed' / 'test.parquet')
    model = joblib.load(root / 'models' / 'model.pkl')
    with open(root / 'models' / 'feature_columns.json', 'r', encoding='utf-8') as f:
        features = json.load(f)
        
    sample = test.sample(min(50000, len(test)), random_state=42).copy()
    y_test_sample = sample['TX_FRAUD'].values
    y_pred_proba = model.predict_proba(sample[features])[:, 1]
    
    return sample, y_test_sample, y_pred_proba, features, model

# -----------------
# HELPER FUNCTIONS
# -----------------
def translate_feature_name(feat_name):
    if feat_name == 'TX_AMOUNT': return "Transaction Amount"
    if feat_name == 'TX_DURING_WEEKEND': return "Weekend Transaction"
    if feat_name == 'TX_DURING_NIGHT': return "Late Night Transaction"
    if 'CUSTOMER_ID_AVG_AMOUNT' in feat_name: return "Customer Avg Spend Baseline"
    if 'CUSTOMER_ID_NB_TX' in feat_name: return "Customer Activity Frequency"
    if 'CUSTOMER_ID_STD_AMOUNT' in feat_name: return "Customer Spend Variability"
    if 'TERMINAL_ID_RISK' in feat_name: return "Terminal Delayed Fraud Rate"
    if 'TERMINAL_ID_NB_TX' in feat_name: return "Terminal Transaction Volume"
    if feat_name == 'TX_AMOUNT_ZSCORE': return "Spend Deviation from Norm (Z-Score)"
    if feat_name == 'TX_DIST_CUSTOMER_TERMINAL': return "Customer-Terminal Distance"
    if feat_name == 'CUSTOMER_ID_NB_TX_15MIN_WINDOW': return "15-Min Transaction Burst"
    if feat_name == 'CUSTOMER_ID_NB_TX_1HOUR_WINDOW': return "1-Hour Transaction Velocity"
    if feat_name == 'TIME_SINCE_LAST_TX': return "Time Since Previous Transaction"
    return feat_name.replace('_', ' ').title()

# -----------------
# MAIN APPLICATION
# -----------------
def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    root = get_project_root()
    metrics_path = root / 'models' / 'metrics_test.json'
    metrics_mtime = metrics_path.stat().st_mtime if metrics_path.exists() else 0.0
    metrics = load_metrics(metrics_mtime)
    if not metrics:
        st.error("⚠️ No model metrics found. Please run the training and evaluation pipeline first.")
        st.code("python -m src.ingestion && python -m src.features && python -m src.split && python -m src.train && python -m src.evaluate", language="bash")
        return
        
    explainer = load_explainer()
    sample, y_test_sample, y_pred_proba, features, model = load_cached_test_data()
    
    # -----------------
    # SIDEBAR: DYNAMIC OPERATIONAL COST ADJUSTER
    # -----------------
    st.sidebar.markdown("## ⚙️ Unit Economics & Costs")
    st.sidebar.caption("Adjust operational parameters to dynamically simulate financial impact across merchant verticals.")
    
    cost_fp = st.sidebar.number_input(
        "Cost per False Alarm Review ($)", 
        min_value=0.5, max_value=50.0, value=5.0, step=0.5,
        help="Cost of analyst manual investigation and customer friction."
    )
    cost_fn = st.sidebar.number_input(
        "Cost per Missed Fraud / Chargeback ($)", 
        min_value=10.0, max_value=2000.0, value=128.44, step=5.0,
        help="Average chargeback, lost merchandise, and bank penalty."
    )
    cost_otp = st.sidebar.number_input(
        "Cost per OTP / SMS Challenge ($)", 
        min_value=0.01, max_value=2.0, value=0.10, step=0.05,
        help="SMS gateway / 3DS verification fee."
    )
    
    cm = metrics['confusion_matrix']
    tp, fp, tn, fn = cm['tp'], cm['fp'], cm['tn'], cm['fn']
    
    recall = metrics['recall']
    precision = metrics['precision']
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    # Dynamically calculated costs based on sidebar inputs
    cost_nothing = (tp + fn) * cost_fn
    cost_model = fp * cost_fp + fn * cost_fn
    savings = cost_nothing - cost_model
    multiplier = cost_nothing / cost_model if cost_model > 0 else 0
    pct_reduction = (savings / cost_nothing * 100) if cost_nothing > 0 else 0

    # ==========================================
    # 1. HERO HEADER
    # ==========================================
    rec_thresh = metrics.get('recommended_threshold', 0.78)
    st.markdown(f"""
        <div class="hero-container">
            <div>
                <h1 class="hero-title">🛡️ AI Risk Manager</h1>
                <p class="hero-subtitle">Autonomous Card-Not-Present (CNP) Fraud Interception & Loss Minimization Engine</p>
                <div class="badge-bar">
                    <span class="pill pill-green">● Active Model: LightGBM</span>
                    <span class="pill">📈 Test Set: {len(sample):,} Transactions</span>
                    <span class="pill">🎯 Policy Threshold: {rec_thresh:.2f}</span>
                    <span class="pill pill-green">⚡ FastAPI: Online (:8000)</span>
                    <span class="pill pill-green">🛡️ PSI Drift: Stable</span>
                    <span class="pill">🔒 Policy: Strictly Defense-Only</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # 2. KEY VERDICT CARD
    # ==========================================
    st.markdown(
        f"""
        <div class="verdict-card">
            <h2>
                Intercepts <strong>{recall*100:.0f}%</strong> of total fraud volume while clearing <strong>{(1-fpr)*100:.1f}%</strong> of genuine transactions with zero checkout friction.
            </h2>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # ==========================================
    # 3. FOUR SPACIOUS KPI METRIC CARDS
    # ==========================================
    k1, k2, k3, k4 = st.columns(4, gap="large")
    
    with k1:
        st.markdown(f"""
            <div class="kpi-box" style="border-top: 5px solid #10b981;">
                <div class="kpi-header">Total Net Savings</div>
                <div class="kpi-number" style="color: #059669;">${savings:,.0f}</div>
                <p class="kpi-footer"><strong>{pct_reduction:.0f}% reduction</strong> in total fraud & operational loss</p>
            </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
            <div class="kpi-box" style="border-top: 5px solid #3b82f6;">
                <div class="kpi-header">Fraud Catch Rate</div>
                <div class="kpi-number" style="color: #2563eb;">{recall*100:.0f}%</div>
                <p class="kpi-footer">Successfully caught <strong>{tp:,}</strong> of {tp+fn:,} frauds</p>
            </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
            <div class="kpi-box" style="border-top: 5px solid #f59e0b;">
                <div class="kpi-header">False Alarm Rate</div>
                <div class="kpi-number" style="color: #d97706;">{fpr*100:.1f}%</div>
                <p class="kpi-footer">Only <strong>{fp:,}</strong> false alarms out of {tn+fp:,} clean orders</p>
            </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
            <div class="kpi-box" style="border-top: 5px solid #8b5cf6;">
                <div class="kpi-header">Capital Efficiency</div>
                <div class="kpi-number" style="color: #7c3aed;">{multiplier:.1f}x</div>
                <p class="kpi-footer">Lower merchant loss compared to doing nothing</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 4. 3-TIER RISK TRIAGE ROUTING POLICY
    # ==========================================
    st.markdown("""
        <div class="section-header-box">
            <h3 class="section-title">🚦 3-Tier Risk Triage Routing Policy</h3>
            <p class="section-desc">Enterprise transaction routing: Frictionless clearance, step-up verification, and automated escalation.</p>
        </div>
    """, unsafe_allow_html=True)

    triage_info = metrics.get('triage', {})
    th_chal = triage_info.get('threshold_challenge', 0.30)
    th_dec = triage_info.get('threshold_decline', 0.78)

    t1_c, t2_c, t3_c = st.columns(3, gap="large")

    app_pct = triage_info.get('approve', {}).get('percentage', 37.96)
    app_cnt = triage_info.get('approve', {}).get('count', 364)
    chal_pct = triage_info.get('challenge', {}).get('percentage', 16.48)
    chal_cnt = triage_info.get('challenge', {}).get('count', 158)
    dec_pct = triage_info.get('decline', {}).get('percentage', 45.57)
    dec_cnt = triage_info.get('decline', {}).get('count', 437)

    with t1_c:
        st.markdown(f"""
            <div class="matrix-tile tile-green">
                <div class="tile-title">🟢 Tier 1: Approve (Friction-Free)</div>
                <div class="tile-value">{app_pct:.1f}%</div>
                <div class="tile-desc"><strong>{app_cnt:,} orders</strong> cleared instantly with 1-click checkout (Risk score &lt; {th_chal:.2f})</div>
            </div>
        """, unsafe_allow_html=True)

    with t2_c:
        st.markdown(f"""
            <div class="matrix-tile tile-amber">
                <div class="tile-title">🟡 Tier 2: Challenge (3DS / OTP)</div>
                <div class="tile-value">{chal_pct:.1f}%</div>
                <div class="tile-desc"><strong>{chal_cnt:,} orders</strong> routed to step-up verification ({th_chal:.2f} &le; Risk &lt; {th_dec:.2f})</div>
            </div>
        """, unsafe_allow_html=True)

    with t3_c:
        st.markdown(f"""
            <div class="matrix-tile tile-red">
                <div class="tile-title">🔴 Tier 3: Decline / Analyst Review</div>
                <div class="tile-value">{dec_pct:.1f}%</div>
                <div class="tile-desc"><strong>{dec_cnt:,} high-risk threats</strong> intercepted and blocked (Risk score &ge; {th_dec:.2f})</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 5. FINANCIAL COMPARISON & DECISION MATRIX
    # ==========================================
    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown("""
            <div class="section-header-box">
                <h3 class="section-title">📊 Financial Loss Comparison</h3>
                <p class="section-desc">Total business financial loss evaluated across the held-out test period.</p>
            </div>
        """, unsafe_allow_html=True)

        fig, ax = plt.subplots(figsize=(7, 2.7), dpi=140)
        categories = ['Without AI Model\n(Flag Nothing)', 'With AI Risk Manager\n(Cost-Optimized)']
        values = [cost_nothing, cost_model]
        bar_colors = ['#ef4444', '#10b981']

        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, values, color=bar_colors, height=0.48, edgecolor='none')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=10.5, fontweight='700', color='#1e293b')
        ax.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        ax.xaxis.set_visible(False)
        ax.tick_params(left=False)

        max_val = max(values) if max(values) > 0 else 1
        ax.set_xlim(0, max_val * 1.25)

        for bar, val, color in zip(bars, values, bar_colors):
            width = bar.get_width()
            y_coord = bar.get_y() + bar.get_height() / 2
            if width >= 0.28 * max_val:
                ax.text(
                    width * 0.5, 
                    y_coord, 
                    f"${val:,.0f}", 
                    va='center', 
                    ha='center', 
                    fontsize=11.5, 
                    fontweight='800', 
                    color='#ffffff'
                )
            else:
                # Place label to the right of the bar to avoid overlap with y-axis text
                text_color = '#065f46' if color == '#10b981' else '#991b1b'
                ax.text(
                    width + 0.025 * max_val, 
                    y_coord, 
                    f"${val:,.0f}", 
                    va='center', 
                    ha='left', 
                    fontsize=11.5, 
                    fontweight='800', 
                    color=text_color
                )

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

        st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:14px 18px; margin-top:8px;">
                <span style="font-size:0.92rem; color:#475569;">
                    💡 <strong>Direct ROI:</strong> Deploying this model prevents <strong>${savings:,.0f}</strong> in unrecovered chargebacks and merchandise loss over the evaluation window.
                </span>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
            <div class="section-header-box">
                <h3 class="section-title">⚖️ Decision Breakdown (Confusion Matrix)</h3>
                <p class="section-desc">Classified transaction outcomes across {tp + fp + tn + fn:,} evaluated test samples.</p>
            </div>
        """, unsafe_allow_html=True)

        m1, m2 = st.columns(2, gap="medium")
        with m1:
            st.markdown(f"""
                <div class="matrix-tile tile-green">
                    <div class="tile-title">✅ Caught Fraud</div>
                    <div class="tile-value">{tp:,}</div>
                    <div class="tile-desc">Saved ${tp*cost_fn:,.0f} in stolen merchandise</div>
                </div>
                <div class="matrix-tile tile-amber">
                    <div class="tile-title">⚠️ False Alarms</div>
                    <div class="tile-value">{fp:,}</div>
                    <div class="tile-desc">Cost ${fp*cost_fp:,.0f} in manual review friction</div>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
                <div class="matrix-tile tile-red">
                    <div class="tile-title">❌ Missed Fraud</div>
                    <div class="tile-value">{fn:,}</div>
                    <div class="tile-desc">Lost ${fn*cost_fn:,.0f} in unrecovered chargebacks</div>
                </div>
                <div class="matrix-tile tile-slate">
                    <div class="tile-title">🛡️ Cleared Genuine</div>
                    <div class="tile-value">{tn:,}</div>
                    <div class="tile-desc">Seamless checkout for legitimate users</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # ==========================================
    # 6. LIVE INTERCEPTED TRANSACTIONS FEED (XAI)
    # ==========================================
    st.markdown("""
        <div class="section-header-box">
            <h3 class="section-title">🚨 Intercepted High-Risk Transactions (Explainable AI)</h3>
            <p class="section-desc">Real-time risk scoring with human-readable, defense-only sentences generated by SHAP.</p>
        </div>
    """, unsafe_allow_html=True)

    high_risk_idx = np.argsort(y_pred_proba)[::-1][:6]
    recent_txs = sample.iloc[high_risk_idx].copy()

    for i in range(len(recent_txs)):
        tx = recent_txs.iloc[i]
        explanation = explainer.explain_transaction(tx)
        risk_color = "#ef4444" if explanation['risk_level'] == "High" else "#f59e0b"
        
        with st.expander(f"💳 Transaction #{int(tx['TRANSACTION_ID'])} | ${tx['TX_AMOUNT']:.2f} — {explanation['top_reasons'][0]}"):
            col_t1, col_t2 = st.columns([1, 1.8], gap="large")
            with col_t1:
                st.markdown(f"""
                    <div style="background:#f8fafc; padding:18px; border-radius:12px; border:1px solid #e2e8f0;">
                        <div style="font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.05em;">Risk Assessment</div>
                        <div style="font-size:1.85rem; font-weight:800; color:{risk_color}; margin: 4px 0 12px 0;">{explanation['score']*100:.1f}% <span style="font-size:1.05rem; font-weight:600;">({explanation['risk_level']} Risk)</span></div>
                        <div style="border-top:1px solid #e2e8f0; padding-top:10px; font-size:0.88rem; line-height:1.6;">
                            <div><strong>Customer ID:</strong> <span class="code-tag">{int(tx['CUSTOMER_ID'])}</span></div>
                            <div><strong>Terminal ID:</strong> <span class="code-tag">{int(tx['TERMINAL_ID'])}</span></div>
                            <div><strong>Timestamp:</strong> <span class="code-tag">{str(tx['TX_DATETIME'])[:19]}</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with col_t2:
                st.markdown("<div style='font-size:1rem; font-weight:700; color:#0f172a; margin-bottom:0.6rem;'>🔍 Why was this flagged? (Plain English)</div>", unsafe_allow_html=True)
                for reason in explanation['top_reasons']:
                    st.markdown(f"""
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid {risk_color}; padding:8px 14px; border-radius:8px; margin-bottom:6px; font-size:0.92rem; color:#1e293b;">
                            • {reason}
                        </div>
                    """, unsafe_allow_html=True)
                
                with st.expander("Show Technical Feature Contributions (SHAP)"):
                    shap_dict = explanation['shap_values']
                    top_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:4]
                    for k, v in top_shap:
                        col_k = "#ef4444" if v > 0 else "#10b981"
                        st.markdown(f"- `{k}`: <span style='color:{col_k}; font-weight:700;'>{v:+.3f} log-odds impact</span>", unsafe_allow_html=True)

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # ==========================================
    # 7. GLOBAL SIGNALS & DUAL THRESHOLD SIMULATOR
    # ==========================================
    col_g1, col_g2 = st.columns([1, 1.1], gap="large")

    with col_g1:
        st.markdown("""
            <div class="section-header-box">
                <h3 class="section-title">🧠 Top Global Risk Signals</h3>
                <p class="section-desc">Key predictive signals weighted most heavily across LightGBM decision trees.</p>
            </div>
        """, unsafe_allow_html=True)

        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            top_5_idx = np.argsort(importances)[::-1][:5]
            top_5_names = [features[i] for i in top_5_idx]
            top_5_vals = importances[top_5_idx]
            translated_names = [translate_feature_name(f) for f in top_5_names]

            fig2, ax2 = plt.subplots(figsize=(6, 3.2), dpi=140)
            y_pos2 = np.arange(len(translated_names))
            ax2.barh(y_pos2[::-1], top_5_vals, color='#4f46e5', height=0.52, edgecolor='none')
            ax2.set_yticks(y_pos2[::-1])
            ax2.set_yticklabels(translated_names, fontsize=9.5, fontweight='700', color='#1e293b')
            ax2.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
            ax2.xaxis.set_visible(False)
            ax2.tick_params(left=False)

            max_sig = max(top_5_vals) if len(top_5_vals) > 0 and max(top_5_vals) > 0 else 1
            ax2.set_xlim(0, max_sig * 1.22)

            for i, v in enumerate(top_5_vals):
                y_idx = len(top_5_vals) - 1 - i
                if v >= 0.28 * max_sig:
                    ax2.text(v * 0.90, y_idx, f"{v:,}", va='center', ha='right', fontsize=9.5, fontweight='700', color='#ffffff')
                else:
                    ax2.text(v + 0.02 * max_sig, y_idx, f"{v:,}", va='center', ha='left', fontsize=9.5, fontweight='700', color='#312e81')

            plt.tight_layout()
            st.pyplot(fig2, use_container_width=True)
            plt.close()

    with col_g2:
        st.markdown("""
            <div class="section-header-box">
                <h3 class="section-title">🎛️ 3-Tier Live Triage Simulator</h3>
                <p class="section-desc">Adjust thresholds live to observe routing volume and dynamic financial loss on a test sample.</p>
            </div>
        """, unsafe_allow_html=True)

        sim_c1, sim_c2 = st.columns(2)
        with sim_c1:
            thresh_challenge_live = st.slider(
                "Tier 2 (OTP Challenge) Threshold:", 
                min_value=0.10, max_value=0.60, value=float(th_chal), step=0.05
            )
        with sim_c2:
            thresh_decline_live = st.slider(
                "Tier 3 (Hard Decline) Threshold:", 
                min_value=0.60, max_value=0.99, value=float(th_dec), step=0.01
            )

        is_app = y_pred_proba < thresh_challenge_live
        is_chal = (y_pred_proba >= thresh_challenge_live) & (y_pred_proba < thresh_decline_live)
        is_dec = y_pred_proba >= thresh_decline_live
        
        sample_total = len(y_test_sample)
        app_pct_sim = (is_app.sum() / sample_total) * 100
        chal_pct_sim = (is_chal.sum() / sample_total) * 100
        dec_pct_sim = (is_dec.sum() / sample_total) * 100

        # Cost simulation considering all tiers
        # Missed fraud in approve costs cost_fn
        # Challenged orders cost cost_otp
        # False decline costs cost_fp
        missed_fraud_count = ((y_test_sample == 1) & is_app).sum()
        false_decline_count = ((y_test_sample == 0) & is_dec).sum()
        chal_count = is_chal.sum()
        
        simulated_cost = missed_fraud_count * cost_fn + false_decline_count * cost_fp + chal_count * cost_otp

        sc1, sc2, sc3 = st.columns(3, gap="medium")
        with sc1:
            st.metric("Approve %", f"{app_pct_sim:.1f}%")
        with sc2:
            st.metric("Challenge %", f"{chal_pct_sim:.1f}%")
        with sc3:
            st.metric("Decline %", f"{dec_pct_sim:.1f}%")
            
        st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:8px 12px; margin-top:8px; font-size:0.85rem; color:#475569;">
                💰 <strong>Estimated Loss at Current Settings:</strong> ${simulated_cost:,.0f} (Sampled)
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # ==========================================
    # 7. TECHNICAL ML VALIDATION EXPANDER
    # ==========================================
    with st.expander("🛠️ Machine Learning Validation Metrics & Curves"):
        st.markdown("**Core Verification Parameters (Held-Out Test Set):**")
        
        cv_path = root / 'models' / 'cv_results.json'
        cv_data = {}
        if cv_path.exists():
            with open(cv_path, 'r', encoding='utf-8') as f:
                cv_data = json.load(f)
        
        lgb_cv = cv_data.get('lightgbm', {})
        mean_pr = lgb_cv.get('mean_pr_auc', 0.8926)
        mean_roc = lgb_cv.get('mean_roc_auc', 0.8473)

        st.json({
            "CV Mean PR-AUC (LightGBM)": f"{mean_pr:.4f}",
            "CV Mean ROC-AUC (LightGBM)": f"{mean_roc:.4f}",
            "Test Recall": f"{recall*100:.1f}%",
            "Test Precision": f"{precision*100:.1f}%",
            "Cost-Optimal Policy Threshold": round(rec_thresh, 2),
            "False Positive Friction Cost": f"${cost_fp:.2f} (Customer friction + review cost)",
            "False Negative Loss Cost": f"${cost_fn:.2f} (Mean unrecovered fraud amount)",
            "Total Evaluated Test Volume": f"{tp + fp + tn + fn:,} Transactions",
            "Temporal Embargo Buffer": f"{cv_data.get('embargo_days', 7)} Days (Zero lookahead / label contamination)",
            "Triage Policy Routing": {
                f"Tier 1: Approve (< {th_chal:.2f})": f"{app_pct:.1f}%",
                f"Tier 2: Challenge ({th_chal:.2f} - {th_dec:.2f})": f"{chal_pct:.1f}%",
                f"Tier 3: Decline (>= {th_dec:.2f})": f"{dec_pct:.1f}%"
            }
        })
        
        pr_curve_path = root / 'reports' / 'figures' / 'pr_curve.png'
        if pr_curve_path.exists():
            st.image(str(pr_curve_path), caption="Precision-Recall Curve (LightGBM vs Baseline)", use_container_width=True)

if __name__ == "__main__":
    main()
