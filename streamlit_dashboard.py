import streamlit as st
import redis
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
from datetime import datetime

st.set_page_config(
    page_title="Vedic Chanting Analyzer",
    page_icon="🕉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .quality-good { color: #00cc88; font-weight: bold; }
    .quality-ok   { color: #ffcc00; font-weight: bold; }
    .quality-bad  { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_redis():
    return redis.Redis(host="localhost", port=6379, decode_responses=True)

r = get_redis()

with st.sidebar:
    st.title("🕉 Vedic Chanting Analyzer")
    st.markdown("---")
    refresh_rate    = st.slider("Refresh Rate (s)",        0.5, 5.0, 1.0, 0.5)
    history_len     = st.slider("History Window (frames)",  20,  200,  80)
    show_raw_hz     = st.checkbox("Pitch Tracking Plot",   value=True)
    show_swara_dist = st.checkbox("Swara Distribution",    value=True)
    show_deviation  = st.checkbox("Deviation Gauge",       value=True)
    st.markdown("---")
    st.markdown("**Swara Reference (Sa = 261.63 Hz)**")
    for s, hz in {
        "Sa": 261.63, "Ri": 294.33, "Ga": 327.03,
        "Ma": 348.83, "Pa": 392.44, "Dha": 436.05, "Ni": 490.55,
    }.items():
        st.markdown(f"`{s}` → {hz:.1f} Hz")

def get_pitch_history(n):
    raw = r.lrange("pitch_history", 0, n - 1)
    records = []
    for item in raw:
        try:
            records.append(json.loads(item))
        except Exception:
            pass
    return list(reversed(records))

def get_latest(key):
    raw = r.get(key)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None

def build_df(history):
    if not history:
        return pd.DataFrame()
    df = pd.DataFrame(history)
    df["index"]           = range(len(df))
    df["frequency_hz"]    = pd.to_numeric(df.get("frequency_hz",    0), errors="coerce").fillna(0)
    df["confidence"]      = pd.to_numeric(df.get("confidence",      0), errors="coerce").fillna(0)
    df["deviation_cents"] = pd.to_numeric(df.get("deviation_cents", 0), errors="coerce").fillna(0)
    df["detected_swara"]  = df.get("detected_swara", "Unknown")
    return df

def quality_color(q):
    q = q.lower()
    if "excellent" in q: return "#00cc88"
    if "good"      in q: return "#88cc00"
    if "needs"     in q: return "#ffcc00"
    return "#ff4444"

SWARA_LINES  = {"Sa": 261.63, "Ri": 294.33, "Ga": 327.03,
                "Ma": 348.83, "Pa": 392.44, "Dha": 436.05, "Ni": 490.55}
SWARA_COLORS = ["#ff6b35","#ffd166","#06d6a0","#118ab2","#ef476f","#8338ec","#3a86ff"]

h1, h2 = st.columns([3, 1])
with h1:
    st.title("🕉 Vedic Chanting Real-Time Analysis")
    st.caption("Live feedback from ROS2 pitch analysis pipeline")
with h2:
    status_ph = st.empty()

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi = {
    "swara":     kpi1.empty(),
    "freq":      kpi2.empty(),
    "conf":      kpi3.empty(),
    "accuracy":  kpi4.empty(),
    "deviation": kpi5.empty(),
}

st.markdown("---")
cc1, cc2 = st.columns([3, 2])
with cc1:
    st.subheader("📈 Real-Time Pitch Tracking")
    pitch_ph = st.empty()
with cc2:
    st.subheader("🎵 Swara Distribution")
    swara_ph = st.empty()

dc, ac = st.columns([2, 3])
with dc:
    st.subheader("🎯 Deviation Gauge")
    gauge_ph = st.empty()
with ac:
    st.subheader("💡 AI Feedback")
    advice_ph = st.empty()

st.markdown("---")
st.subheader("📋 Session Log")
log_ph = st.empty()

session_log = deque(maxlen=20)

while True:
    history  = get_pitch_history(history_len)
    feedback = get_latest("latest_feedback")
    latest   = get_latest("latest_pitch")
    df       = build_df(history)

    status_ph.success("🟢 Live") if latest else status_ph.warning("🟡 Waiting for ROS2...")

    if latest:
        kpi["swara"].metric("Current Swara", latest.get("detected_swara", "—"))
        kpi["freq"].metric("Frequency (Hz)", f"{latest.get('frequency_hz', 0):.1f}")
        kpi["conf"].metric("Confidence",     f"{latest.get('confidence', 0)*100:.0f}%")
    if feedback and feedback.get("status") == "active":
        kpi["accuracy"].metric("Session Accuracy", f"{feedback.get('accuracy_percent', 0)}%")
        kpi["deviation"].metric("Avg Deviation",   f"{feedback.get('avg_deviation_cents', 0):.1f} ¢")

    if show_raw_hz and not df.empty:
        fig = go.Figure()
        for (swara, ref_hz), color in zip(SWARA_LINES.items(), SWARA_COLORS):
            fig.add_hline(y=ref_hz, line_dash="dot", line_color=color,
                          annotation_text=swara, annotation_position="right",
                          line_width=1, opacity=0.6)
        fig.add_trace(go.Scatter(
            x=df["index"], y=df["frequency_hz"],
            mode="lines+markers", name="Pitch (Hz)",
            line=dict(color="#ff6b35", width=2),
            marker=dict(size=5, color=df["confidence"], colorscale="RdYlGn",
                        cmin=0, cmax=1, showscale=True,
                        colorbar=dict(title="Confidence", len=0.5)),
            hovertemplate="Hz: %{y:.1f}<br>Swara: %{text}<extra></extra>",
            text=df["detected_swara"],
        ))
        fig.update_layout(template="plotly_dark", height=320,
                          margin=dict(l=10, r=80, t=20, b=30),
                          xaxis_title="Frame", yaxis_title="Frequency (Hz)",
                          yaxis=dict(range=[200, 550]), showlegend=False)
        pitch_ph.plotly_chart(fig, use_container_width=True)

    if show_swara_dist and not df.empty:
        valid = df[df["detected_swara"] != "Silence"]
        if not valid.empty:
            sc = valid["detected_swara"].value_counts().reset_index()
            sc.columns = ["Swara", "Count"]
            fig2 = px.bar(sc, x="Swara", y="Count", color="Swara",
                          color_discrete_sequence=SWARA_COLORS,
                          template="plotly_dark", height=320)
            fig2.update_layout(margin=dict(l=10, r=10, t=20, b=30), showlegend=False)
            swara_ph.plotly_chart(fig2, use_container_width=True)

    if show_deviation and feedback and feedback.get("status") == "active":
        avg_dev = feedback.get("avg_deviation_cents", 0)
        fig3 = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=avg_dev,
            title={"text": "Avg Deviation (cents)", "font": {"color": "white"}},
            delta={"reference": 15,
                   "increasing": {"color": "#ff4444"},
                   "decreasing": {"color": "#00cc88"}},
            gauge={
                "axis":  {"range": [0, 100], "tickcolor": "white"},
                "bar":   {"color": quality_color(feedback.get("quality", ""))},
                "steps": [
                    {"range": [0,  15],  "color": "#003300"},
                    {"range": [15, 30],  "color": "#333300"},
                    {"range": [30, 50],  "color": "#330000"},
                    {"range": [50, 100], "color": "#550000"},
                ],
                "threshold": {"line": {"color": "white", "width": 2},
                              "thickness": 0.75, "value": 30},
            },
        ))
        fig3.update_layout(template="plotly_dark", height=300,
                           margin=dict(l=20, r=20, t=40, b=20),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        gauge_ph.plotly_chart(fig3, use_container_width=True)

    if feedback and feedback.get("status") == "active":
        q     = feedback.get("quality", "")
        color = quality_color(q)
        advice_ph.markdown(f"""
<div style="background:#1e1e2e; border-left:4px solid {color};
            padding:1.2rem; border-radius:8px; margin-top:0.5rem;">
  <p style="font-size:1.1rem; color:{color}; margin:0 0 0.5rem 0;"><b>{q}</b></p>
  <p style="color:#cccccc; margin:0 0 0.5rem 0;">
    🎵 <b>Dominant Swara:</b> {feedback.get("dominant_swara","—")}</p>
  <p style="color:#cccccc; margin:0 0 0.5rem 0;">
    📊 <b>Pitch Trend:</b> {feedback.get("pitch_trend","—")}</p>
  <p style="color:#ffffff; margin:0; font-size:1rem; font-style:italic;">
    💡 {feedback.get("advice","—")}</p>
</div>
""", unsafe_allow_html=True)

    if latest and latest.get("detected_swara") not in ("Silence", None):
        session_log.appendleft({
            "Time":       datetime.now().strftime("%H:%M:%S"),
            "Swara":      latest.get("detected_swara", "—"),
            "Hz":         f"{latest.get('frequency_hz', 0):.1f}",
            "Deviation":  f"{latest.get('deviation_cents', 0):.1f} ¢",
            "Confidence": f"{latest.get('confidence', 0)*100:.0f}%",
        })
    if session_log:
        log_ph.dataframe(pd.DataFrame(session_log),
                         use_container_width=True, hide_index=True)

    time.sleep(refresh_rate)
