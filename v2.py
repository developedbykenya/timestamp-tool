# lyrics_timestamping_studio.py
import streamlit as st
import time
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import librosa
import soundfile as sf
import tempfile

# --------------------------
# Utility Functions
# --------------------------

def format_time(seconds: float) -> str:
    """Format float seconds into SRT timestamp (HH:MM:SS,ms)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"

def generate_waveform(audio_bytes):
    """
    Load audio from bytes and return waveform data for Plotly.
    Works for mp3, wav, webm, etc.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name

    try:
        # Try with soundfile first (works for WAV, FLAC)
        y, sr = sf.read(tmp_path)
    except:
        # Fallback to librosa for MP3, WebM, etc.
        y, sr = librosa.load(tmp_path, sr=None, mono=True)

    duration = len(y) / sr
    times = np.linspace(0, duration, num=len(y))
    return times, y

def create_srt(timestamps):
    """Generate SRT text from timestamp DataFrame."""
    srt_output = ""
    for i, row in timestamps.iterrows():
        start = row["start"]
        end = row["end"]
        text = row["lyric"]
        srt_output += f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n"
    return srt_output

# --------------------------
# Streamlit App Layout
# --------------------------
st.set_page_config(page_title="Lyrics Timestamping Studio", page_icon="🎶", layout="wide")

st.title("🎶 Lyrics Timestamping Studio → .SRT")
st.markdown(
    """
    **Sync your lyrics, audio, and export professional `.srt` subtitle files.**
    - 🎤 *Musicians & Lyric Video Creators* — perfect manual control  
    - 🎧 *Podcasters / YouTubers* — generate captions effortlessly  
    - 🏢 *Studios* — integrate AI or cloud sync for teams
    """
)

# --------------------------
# Step 1: Upload Files
# --------------------------
st.header("1️⃣ Upload Lyrics & Audio")

lyrics_file = st.file_uploader("Upload Lyrics (.txt)", type=["txt"])
audio_file = st.file_uploader("Upload Audio (mp3/wav/webm)", type=["mp3", "wav", "webm"])

lyrics = []
if lyrics_file:
    lyrics = [line.strip() for line in lyrics_file.read().decode("utf-8").splitlines() if line.strip()]
    st.success(f"✅ Loaded {len(lyrics)} lyric lines.")

if audio_file:
    st.audio(audio_file, format="audio/mp3")

# --------------------------
# Step 2: Waveform Visualization
# --------------------------
if audio_file:
    st.header("2️⃣ Waveform Preview")
    try:
        times, y = generate_waveform(audio_file.getvalue())
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=y, mode="lines", line=dict(color="royalblue")))
        fig.update_layout(title="Audio Waveform", xaxis_title="Time (s)", yaxis_title="Amplitude", height=200)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning("⚠️ Could not generate waveform. Proceeding without visualization.")
        st.text(str(e))


# --------------------------
# Initialize Session State
# --------------------------
if "timestamps" not in st.session_state:
    st.session_state.timestamps = pd.DataFrame(columns=["start", "end", "lyric"])
if "current_line" not in st.session_state:
    st.session_state.current_line = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "paused_time" not in st.session_state:
    st.session_state.paused_time = None
if "is_paused" not in st.session_state:
    st.session_state.is_paused = False

# --------------------------
# Step 3: Manual Timestamping
# --------------------------
st.header("3️⃣ Manual Timestamping")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Start / Restart") and lyrics and audio_file:
        st.session_state.timestamps = pd.DataFrame(columns=["start", "end", "lyric"])
        st.session_state.current_line = 0
        st.session_state.start_time = time.time()
        st.session_state.is_paused = False
        st.info("Audio playing in browser. Click 'Mark Timestamp' for each lyric.")

with col2:
    if st.button("⏸ Pause") and st.session_state.start_time:
        if not st.session_state.is_paused:
            st.session_state.paused_time = time.time()
            st.session_state.is_paused = True
            st.warning("Paused.")

with col3:
    if st.button("▶ Resume") and st.session_state.is_paused:
        offset = time.time() - st.session_state.paused_time
        st.session_state.start_time += offset
        st.session_state.is_paused = False
        st.success("Resumed.")

# Mark timestamps
if st.session_state.start_time and not st.session_state.is_paused and st.session_state.current_line < len(lyrics):
    if st.button("✅ Mark Timestamp"):
        elapsed = time.time() - st.session_state.start_time
        line = lyrics[st.session_state.current_line]
        prev_end = elapsed + 2.0  # default 2s end offset
        st.session_state.timestamps.loc[len(st.session_state.timestamps)] = [elapsed, prev_end, line]
        st.session_state.current_line += 1
        st.success(f"Line {st.session_state.current_line}/{len(lyrics)} recorded.")

# --------------------------
# Step 4: Editable Timestamps
# --------------------------
if len(st.session_state.timestamps) > 0:
    st.header("4️⃣ Review & Edit Timestamps")
    edited_df = st.data_editor(st.session_state.timestamps, num_rows="dynamic", use_container_width=True)
    st.session_state.timestamps = edited_df

# --------------------------
# Step 5: Export SRT
# --------------------------
if len(st.session_state.timestamps) > 0:
    st.header("5️⃣ Export")
    srt_output = create_srt(st.session_state.timestamps)
    st.download_button("💾 Download .SRT", srt_output, file_name="lyrics.srt", mime="text/plain")
    with st.expander("Preview SRT"):
        st.code(srt_output[:800] + ("..." if len(srt_output) > 800 else ""), language="srt")

# --------------------------
# Step 6: Pro / Cloud Options
# --------------------------
st.header("💡 Coming Soon: Pro Features")

st.markdown(
    """
    - 🤖 **AI Auto-Timestamping (Pro)** — automatically align lyrics using speech-to-text (Whisper API).  
    - ☁️ **Cloud Save / Team Projects** — save, share, and collaborate online.  
    - 💳 **Upgrade to Premium** — unlock AI + cloud features.  
    """
)

st.button("🚀 Try AI Auto-Timestamping (Pro Placeholder)")
st.button("☁️ Save Project to Cloud (Placeholder)")
