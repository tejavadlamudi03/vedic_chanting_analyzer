import streamlit as st
import redis
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from collections import deque
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🕉 Vedic Chanting Analyzer",
    page_icon="🕉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Redis connection ──────────────────────────────────────────────────────────
@st.cache_resource
def get_redis():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)

r = get_redis()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border: 1px solid #ff6b35;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .swara-badge {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ff6b35;
    }
    .quality-good  { color: #00cc88; font-weight: bold; }
    .quality-ok    { color: #ffcc00; font-weight: bold; }
    .quality-bad   { color: #ff4444; font-weight: bold; }
    .stMetric label { font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🕉 Vedic Chanting Analyzer")
    st.markdown("---")
    refresh_rate = st.slider("Refresh Rate (seconds)", 0.5, 5.0, 1.0, 0.5)
    history_len  = st.slider("History Window (frames)", 20, 200, 80)
    show_raw_hz  = st.checkbox("Show Raw Hz Plot", value=True)
    show_swara_dist = st.checkbox("Show Swara Distribution", value=True)
    show_deviation  = st.checkbox("Show Deviation Gauge", value=True)
    st.markdown("---")
    st.markdown("**Swara Reference (Sa = 261.63 Hz)**")
    swara_ref = {
        'Sa': 261.63, 'Ri': 294.33, 'Ga': 327.03,
        'Ma': 348.83, 'Pa': 392.44, 'Dha': 436.05, 'Ni': 490.55
    }
    for s, hz in swara_ref.items():
        st.markdown(f"`{s}` → {hz:.1f} Hz")

# ── Helper: fetch data from Redis ─────────────────────────────────────────────
def get_pitch_history(n=history_len):
    raw = r.lrange('pitch_history', 0, n - 1)
    records = []
    for item in raw:
        try:
            d = json.loads(item)
            records.append(d)
        except Exception:
            pass
    return list(reversed(records))  # oldest first

def get_latest_feedback():
    raw = r.get('latest_feedback')
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None

def get_latest_pitch():
    raw = r.get('latest_pitch')
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None

# ── Build pitch DataFrame ──────────────────────────────────────────────────────
def build_df(history):
    if not history:
        return pd.DataFrame()
    df = pd.DataFrame(history)
    df['index'] = range(len(df))
    df['frequency_hz']    = pd.to_numeric(df.get('frequency_hz', 0), errors='coerce').fillna(0)
    df['confidence']      = pd.to_numeric(df.get('confidence', 0), errors='coerce').fillna(0)
    df['deviation_cents'] = pd.to_numeric(df.get('deviation_cents', 0), errors='coerce').fillna(0)
    df['detected_swara']  = df.get('detected_swara', 'Unknown')
    return df

# ── Quality color helper ───────────────────────────────────────────────────────
def quality_color(quality_str):
    q = quality_str.lower()
    if 'excellent' in q:  return '#00cc88'
    if 'good'      in q:  return '#88cc00'
    if 'needs'     in q:  return '#ffcc00'
    return '#ff4444'

# ── Main UI ───────────────────────────────────────────────────────────────────
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("🕉 Vedic Chanting Real-Time Analysis")
    st.caption("Live feedback from ROS2 pitch analysis pipeline")
with header_col2:
    status_placeholder = st.empty()

# ── KPI Row ───────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi_placeholders = {
    'swara':    kpi1.empty(),
    'freq':     kpi2.empty(),
    'conf':     kpi3.empty(),
    'accuracy': kpi4.empty(),
    'deviation':kpi5.empty(),
}

# ── Charts Row ────────────────────────────────────────────────────────────────
st.markdown("---")

chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.subheader("📈 Real-Time Pitch Tracking")
    pitch_chart = st.empty()

with chart_col2:
    st.subheader("🎵 Swara Distribution")
    swara_chart = st.empty()

# ── Second row ────────────────────────────────────────────────────────────────
dev_col, advice_col = st.columns([2, 3])

with dev_col:
    st.subheader("🎯 Deviation Gauge")
    dev_gauge = st.empty()

with advice_col:
    st.subheader("💡 AI Feedback")
    advice_box = st.empty()

# ── Session log ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Session Log")
log_table = st.empty()

# ── Swara reference lines for pitch chart ─────────────────────────────────────
SWARA_LINES = {
    'Sa': 261.63, 'Ri': 294.33, 'Ga': 327.03,
    'Ma': 348.83, 'Pa': 392.44, 'Dha': 436.05, 'Ni': 490.55
}
SWARA_COLORS = ['#ff6b35','#ffd166','#06d6a0','#118ab2','#ef476f','#8338ec','#3a86ff']

# ── Main loop ─────────────────────────────────────────────────────────────────
session_log = deque(maxlen=20)

while True:
    # ── Fetch data ────────────────────────────────────────────────────────────
    history  = get_pitch_history(history_len)
    feedback = get_latest_feedback()
    latest   = get_latest_pitch()
    df       = build_df(history)

    # ── Connection status ─────────────────────────────────────────────────────
    if latest:
        status_placeholder.success("🟢 Live")
    else:
        status_placeholder.warning("🟡 Waiting for ROS2...")

    # ── KPI metrics ───────────────────────────────────────────────────────────
    if latest:
        kpi_placeholders['swara'].metric(
            "Current Swara", latest.get('detected_swara', '—'))
        kpi_placeholders['freq'].metric(
            "Frequency (Hz)", f"{latest.get('frequency_hz', 0):.1f}")
        kpi_placeholders['conf'].metric(
            "Confidence", f"{latest.get('confidence', 0)*100:.0f}%")

    if feedback and feedback.get('status') == 'active':
        kpi_placeholders['accuracy'].metric(
            "Session Accuracy", f"{feedback.get('accuracy_percent', 0)}%")
        kpi_placeholders['deviation'].metric(
            "Avg Deviation", f"{feedback.get('avg_deviation_cents', 0):.1f} ¢")

    # ── Pitch chart ───────────────────────────────────────────────────────────
    if show_raw_hz and not df.empty:
        fig_pitch = go.Figure()

        # Reference swara lines
        for (swara, ref_hz), color in zip(SWARA_LINES.items(), SWARA_COLORS):
            fig_pitch.add_hline(
                y=ref_hz, line_dash="dot", line_color=color,
                annotation_text=swara, annotation_position="right",
                line_width=1, opacity=0.6)

        # Pitch curve — color by confidence
        fig_pitch.add_trace(go.Scatter(
            x=df['index'],
            y=df['frequency_hz'],
            mode='lines+markers',
            name='Pitch (Hz)',
            line=dict(color='#ff6b35', width=2),
            marker=dict(
                size=5,
                color=df['confidence'],
                colorscale='RdYlGn',
                cmin=0, cmax=1,
                showscale=True,
                colorbar=dict(title='Confidence', len=0.5)
            ),
            hovertemplate='Hz: %{y:.1f}<br>Swara: %{text}<extra></extra>',
            text=df['detected_swara']
        ))

        fig_pitch.update_layout(
            template='plotly_dark',
            height=320,
            margin=dict(l=10, r=80, t=20, b=30),
            xaxis_title="Frame",
            yaxis_title="Frequency (Hz)",
            yaxis=dict(range=[200, 550]),
            showlegend=False
        )
        pitch_chart.plotly_chart(fig_pitch, use_container_width=True)

    # ── Swara distribution ────────────────────────────────────────────────────
    if show_swara_dist and not df.empty:
        valid = df[df['detected_swara'] != 'Silence']
        if not valid.empty:
            swara_counts = valid['detected_swara'].value_counts().reset_index()
            swara_counts.columns = ['Swara', 'Count']

            fig_swara = px.bar(
                swara_counts, x='Swara', y='Count',
                color='Swara',
                color_discrete_sequence=SWARA_COLORS,
                template='plotly_dark',
                height=320
            )
            fig_swara.update_layout(
                margin=dict(l=10, r=10, t=20, b=30),
                showlegend=False
            )
            swara_chart.plotly_chart(fig_swara, use_container_width=True)

    # ── Deviation gauge ───────────────────────────────────────────────────────
    if show_deviation and feedback and feedback.get('status') == 'active':
        avg_dev = feedback.get('avg_deviation_cents', 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_dev,
            title={'text': "Avg Deviation (cents)", 'font': {'color': 'white'}},
            delta={'reference': 15, 'increasing': {'color': '#ff4444'},
                                    'decreasing': {'color': '#00cc88'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'white'},
                'bar':  {'color': quality_color(feedback.get('quality', ''))},
                'steps': [
                    {'range': [0, 15],  'color': '#003300'},
                    {'range': [15, 30], 'color': '#333300'},
                    {'range': [30, 50], 'color': '#330000'},
                    {'range': [50, 100],'color': '#550000'},
                ],
                'threshold': {
                    'line': {'color': 'white', 'width': 2},
                    'thickness': 0.75, 'value': 30
                }
            }
        ))
        fig_gauge.update_layout(
            template='plotly_dark', height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        dev_gauge.plotly_chart(fig_gauge, use_container_width=True)

    # ── AI Feedback advice box ─────────────────────────────────────────────────
    if feedback and feedback.get('status') == 'active':
        q = feedback.get('quality', '')
        color = quality_color(q)
        advice_box.markdown(f"""
<div style="background:#1e1e2e; border-left: 4px solid {color};
            padding: 1.2rem; border-radius: 8px; margin-top: 0.5rem;">
  <p style="font-size:1.1rem; color:{color}; margin:0 0 0.5rem 0;">
    <b>{q}</b>
  </p>
  <p style="color:#cccccc; margin:0 0 0.5rem 0;">
    🎵 <b>Dominant Swara:</b> {feedback.get('dominant_swara', '—')}
  </p>
  <p style="color:#cccccc; margin:0 0 0.5rem 0;">
    📊 <b>Pitch Trend:</b> {feedback.get('pitch_trend', '—')}
  </p>
  <p style="color:#ffffff; margin:0; font-size:1rem; font-style: italic;">
    💡 {feedback.get('advice', '—')}
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Session log table ─────────────────────────────────────────────────────
    if latest and latest.get('detected_swara') not in ('Silence', None):
        session_log.appendleft({
            'Time':     datetime.now().strftime('%H:%M:%S'),
            'Swara':    latest.get('detected_swara', '—'),
            'Hz':       f"{latest.get('frequency_hz', 0):.1f}",
            'Deviation':f"{latest.get('deviation_cents', 0):.1f} ¢",
            'Confidence':f"{latest.get('confidence', 0)*100:.0f}%",
        })
    if session_log:
        log_table.dataframe(
            pd.DataFrame(session_log),
            use_container_width=True,
            hide_index=True
        )

    time.sleep(refresh_rate)
