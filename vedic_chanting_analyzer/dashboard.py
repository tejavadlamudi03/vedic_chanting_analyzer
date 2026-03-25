#!/usr/bin/env python3
import streamlit as st
import json
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import deque
from pathlib import Path

st.set_page_config(
    page_title="Vedic Chanting Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { color: #ffffff; }
    [data-testid="stMetric"] {
        background-color: #1e2530;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

PITCH_FILE    = Path('/tmp/vedic_pitch.json')
FEEDBACK_FILE = Path('/tmp/vedic_feedback.json')

SWARA_ORDER = [
    'Sa', 'Ri1', 'Ri2', 'Ga1', 'Ga2', 'Ga3',
    'Ma1', 'Ma2', 'Pa', 'Dha1', 'Dha2', 'Ni1', 'Ni2', 'Ni3'
]

SWARA_FREQ = {
    'Sa':   261.63, 'Ri1': 272.54, 'Ri2': 294.33,
    'Ga1':  308.25, 'Ga2': 327.03, 'Ga3': 348.83,
    'Ma1':  348.83, 'Ma2': 367.92, 'Pa':  392.00,
    'Dha1': 408.96, 'Dha2':436.05, 'Ni1': 457.69,
    'Ni2':  490.55, 'Ni3': 523.25,
}

SWARA_COLORS = {
    'Sa':   '#e74c3c', 'Ri1': '#e67e22', 'Ri2': '#d35400',
    'Ga1':  '#f1c40f', 'Ga2': '#f39c12', 'Ga3': '#d4ac0d',
    'Ma1':  '#2ecc71', 'Ma2': '#27ae60', 'Pa':  '#1abc9c',
    'Dha1': '#3498db', 'Dha2':'#2471a3', 'Ni1': '#9b59b6',
    'Ni2':  '#8e44ad', 'Ni3': '#6c3483',
}

SWARA_HINDI = {
    'Sa':   'सा',  'Ri1': 'रे॒', 'Ri2': 'रे',
    'Ga1':  'ग॒',  'Ga2': 'ग',   'Ga3': 'ग॑',
    'Ma1':  'म',   'Ma2': 'म॑',  'Pa':  'प',
    'Dha1': 'ध॒',  'Dha2':'ध',   'Ni1': 'नि॒',
    'Ni2':  'नि',  'Ni3': 'नि॑',
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def read_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ── Chart: Frequency Wave ─────────────────────────────────────────────────────
def make_freq_wave(history):
    if len(history) < 2:
        return go.Figure()

    df    = pd.DataFrame(history)
    freqs = df['Frequency (Hz)'].values
    n     = len(freqs)
    x     = np.linspace(0, 4 * np.pi, n)

    amp   = (freqs - freqs.min()) / (freqs.max() - freqs.min() + 1e-6)
    amp   = 0.3 + amp * 0.7
    inner = amp * np.sin(x * 6)
    outer = amp * np.sin(x * 2) * 1.4

    fig = go.Figure()
    for y_line in [-1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2]:
        fig.add_hline(y=y_line,
                      line=dict(color='rgba(255,255,255,0.07)', width=1, dash='dot'))

    fig.add_trace(go.Scatter(x=np.arange(n), y=outer, mode='lines',
        line=dict(color='rgba(100,220,255,0.5)', width=2, dash='dash'),
        showlegend=False))
    fig.add_trace(go.Scatter(x=np.arange(n), y=-outer, mode='lines',
        line=dict(color='rgba(100,220,255,0.5)', width=2, dash='dash'),
        showlegend=False))
    fig.add_trace(go.Scatter(x=np.arange(n), y=inner, mode='lines',
        line=dict(color='rgba(100,200,255,0.3)', width=8),
        showlegend=False))
    fig.add_trace(go.Scatter(x=np.arange(n), y=inner, mode='lines',
        line=dict(color='rgba(255,255,255,1.0)', width=2.5),
        fill='tonexty', fillcolor='rgba(255,255,255,0.03)',
        showlegend=False))

    fig.update_layout(
        paper_bgcolor='#0a0f1e', plot_bgcolor='#0d1527',
        font=dict(color='white'),
        margin=dict(l=10, r=10, t=10, b=10),
        height=280, showlegend=False,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                   zeroline=False, showticklabels=False, title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   zerolinewidth=1, showticklabels=False,
                   range=[-1.8, 1.8], title=''),
    )
    return fig


# ── Chart: Swara Tone Distribution ────────────────────────────────────────────
def make_swara_chart(counts):
    swaras = SWARA_ORDER
    values = [counts.get(s, 0) for s in swaras]
    colors = [SWARA_COLORS.get(s, '#95a5a6') for s in swaras]
    hindi  = [SWARA_HINDI.get(s, s) for s in swaras]
    freqs  = [SWARA_FREQ.get(s, 0) for s in swaras]
    labels = [f"{s} ({h})  {f:.0f} Hz"
              for s, h, f in zip(swaras, hindi, freqs)]

    active = max(counts, key=counts.get) if counts else None
    fig    = go.Figure()

    for i, swara in enumerate(swaras):
        is_active = (swara == active and values[i] > 0)
        fig.add_trace(go.Bar(
            y=[labels[i]], x=[values[i]], orientation='h',
            marker=dict(
                color=colors[i],
                opacity=1.0 if is_active else 0.55,
                line=dict(color='white' if is_active else '#0e1117',
                          width=2 if is_active else 0.5)
            ),
            text=f" {values[i]}" if values[i] > 0 else '',
            textposition='outside',
            textfont=dict(color='white', size=11),
            showlegend=False, name=swara
        ))

    fig.update_layout(
        paper_bgcolor='#1e2530', plot_bgcolor='#1e2530',
        font=dict(color='white', size=12),
        margin=dict(l=10, r=40, t=10, b=10), height=420,
        barmode='overlay',
        xaxis=dict(title='Count', gridcolor='#2c3e50',
                   color='white', showgrid=True),
        yaxis=dict(color='white', tickfont=dict(size=11),
                   autorange='reversed'),
    )
    return fig


# ── Chart: Deviation Over Time ────────────────────────────────────────────────
def make_deviation_chart(history):
    if len(history) < 2:
        return go.Figure()

    df   = pd.DataFrame(history)
    x    = np.arange(len(df))
    devs = df['Deviation'].values

    fig = go.Figure()
    fig.add_hrect(y0=-50, y1=50,
                  fillcolor='rgba(46,204,113,0.15)', line_width=0,
                  annotation_text="✅ Acceptable zone",
                  annotation_font_color='#2ecc71')
    fig.add_trace(go.Scatter(
        x=x, y=devs, mode='lines+markers',
        line=dict(color='#9b59b6', width=2),
        marker=dict(size=4, color='#e74c3c'),
        fill='tozeroy', fillcolor='rgba(155,89,182,0.1)',
        name='Deviation (¢)'
    ))
    fig.add_hline(y=0, line_dash='dash',
                  line_color='#2ecc71', line_width=1.5)
    fig.update_layout(
        paper_bgcolor='#1e2530', plot_bgcolor='#1e2530',
        font=dict(color='white'),
        margin=dict(l=10, r=10, t=10, b=10), height=200,
        xaxis=dict(title='Frames', gridcolor='#2c3e50', color='white'),
        yaxis=dict(title='Cents',  gridcolor='#2c3e50', color='white'),
    )
    return fig


# ── Live Swara Box ────────────────────────────────────────────────────────────
def render_live_swara(placeholder, sw, hz, dev):
    if sw not in ('Silence', '—', 'Unknown') and hz > 60:
        color    = SWARA_COLORS.get(sw, '#ffffff')
        hindi    = SWARA_HINDI.get(sw, '')
        freq_val = SWARA_FREQ.get(sw, hz)
        placeholder.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e2530, #0e1117);
            border: 2px solid {color};
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 0 30px {color}55;
        ">
            <div style="font-size: 90px; font-weight: bold;
                        color: {color}; line-height: 1;">
                {sw}
            </div>
            <div style="font-size: 52px; color: {color}99; margin-top: 8px;">
                {hindi}
            </div>
            <div style="font-size: 20px; color: #aaaaaa; margin-top: 12px;">
                🎵 {hz:.1f} Hz &nbsp;|&nbsp; Target: {freq_val:.1f} Hz
                &nbsp;|&nbsp; Deviation: {dev:+.1f} ¢
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        placeholder.markdown("""
        <div style="
            background: #1e2530;
            border: 2px dashed #444;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
        ">
            <div style="font-size: 48px; color: #555;">— Silence —</div>
        </div>
        """, unsafe_allow_html=True)


# ── UI Layout ─────────────────────────────────────────────────────────────────
st.title("🕉 Vedic Chanting Real-Time Analysis")
st.caption("Live feedback from ROS2 pitch analysis pipeline")

status_ph = st.empty()
st.divider()

c1, c2, c3, c4 = st.columns(4)
freq_ph     = c1.empty()
swara_ph    = c2.empty()
dev_ph      = c3.empty()
conf_ph     = c4.empty()

st.divider()
st.subheader("🎤 Currently Singing")
live_swara_ph = st.empty()

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("📈 Real-Time Frequency Wave")
    freq_chart = st.empty()
with col2:
    st.subheader("🎵 Swara Tone Distribution")
    swara_chart = st.empty()

st.divider()
st.subheader("📉 Pitch Deviation Over Time")
dev_chart = st.empty()

st.divider()
st.subheader("💡 AI Feedback")
fa, fb, fc  = st.columns(3)
quality_ph  = fa.empty()
accuracy_ph = fb.empty()
avgdev_ph   = fc.empty()
advice_ph   = st.empty()


# ── Buffers ───────────────────────────────────────────────────────────────────
freq_history = deque(maxlen=200)
swara_counts = {}
loop_count   = 0
CHART_REFRESH = 10   # charts refresh every 10 loops = ~3s (no flicker)


# ── Live Loop ─────────────────────────────────────────────────────────────────
while True:
    pitch      = read_json(PITCH_FILE)
    feedback   = read_json(FEEDBACK_FILE)
    loop_count += 1

    if pitch:
        status_ph.success("🟢 Live — Receiving ROS2 data")

        hz   = pitch.get('frequency_hz', 0)
        sw   = pitch.get('detected_swara', '—')
        dev  = pitch.get('deviation_cents', 0)
        conf = pitch.get('confidence', 0)

        # ── Fast updates every 0.3s ───────────────────────────────────
        freq_ph.metric("🎵 Frequency",  f"{hz:.2f} Hz")
        swara_ph.metric("🎼 Swara",     sw)
        dev_ph.metric("📏 Deviation",   f"{dev:.1f} ¢",
                      delta=f"{'↑ sharp' if dev > 0 else '↓ flat'}")
        conf_ph.metric("✅ Confidence", f"{conf:.2f}")

        render_live_swara(live_swara_ph, sw, hz, dev)

        # Update history
        if hz > 60:
            freq_history.append({
                'Frequency (Hz)': hz,
                'Deviation':      dev,
                'Confidence':     conf
            })
        if sw not in ('Silence', '—', 'Unknown'):
            swara_counts[sw] = swara_counts.get(sw, 0) + 1

        # ── Slow chart updates every ~3s (no flicker) ─────────────────
        if loop_count % CHART_REFRESH == 0:
            freq_chart.plotly_chart(make_freq_wave(freq_history),
                                    use_container_width=True)
            swara_chart.plotly_chart(make_swara_chart(swara_counts),
                                     use_container_width=True)
            dev_chart.plotly_chart(make_deviation_chart(freq_history),
                                   use_container_width=True)

    else:
        status_ph.warning("⏳ Waiting for ROS2... Run the launch file.")
        render_live_swara(live_swara_ph, '—', 0, 0)

    if feedback and feedback.get('status') == 'active':
        quality_ph.metric("🎯 Quality",   feedback.get('quality', '—'))
        accuracy_ph.metric("📊 Accuracy", f"{feedback.get('accuracy_percent', 0)}%")
        avgdev_ph.metric("📉 Avg Dev",    f"{feedback.get('avg_deviation_cents', 0)} ¢")
        advice_ph.info(f"🗣 {feedback.get('advice', '')}")

    time.sleep(0.3)
