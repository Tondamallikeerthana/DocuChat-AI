"""
Local video transcription + chunking for the RAG pipeline.

Pulls audio out of local video files (no YouTube), transcribes it with
faster-whisper, and groups the raw transcript segments into timestamp-aware
chunks that slot into the same Document format used for PDFs/docx/etc.

Requirements:
    pip install faster-whisper
    ffmpeg must be installed on the system and on PATH
        (Ubuntu/Debian: sudo apt install ffmpeg)
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.documents import Document

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}

_whisper_model = None


def _get_whisper_model(model_size: str = "base"):
    """Lazily load the faster-whisper model once and reuse it across videos."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print(f"[INFO] Loading faster-whisper model: {model_size}")
        # device="cpu", compute_type="int8" works without a GPU.
        # If you have a CUDA GPU, switch to device="cuda", compute_type="float16".
        _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper_model


def extract_audio(video_path: str) -> str:
    """Extract a temporary 16kHz mono wav track from a video file using ffmpeg."""
    audio_path = os.path.join(tempfile.gettempdir(), Path(video_path).stem + "_audio.wav")
    cmd = f'ffmpeg -y -i "{video_path}" -ac 1 -ar 16000 -vn "{audio_path}" -loglevel error'
    ret = os.system(cmd)
    if ret != 0 or not os.path.exists(audio_path):
        raise RuntimeError(f"ffmpeg failed to extract audio from {video_path}")
    return audio_path


def transcribe_video(video_path: str, model_size: str = "base") -> List[Dict[str, Any]]:
    """Transcribe a local video file. Returns a list of {text, start, end} segments."""
    model = _get_whisper_model(model_size)
    audio_path = extract_audio(video_path)
    try:
        segments, info = model.transcribe(audio_path, beam_size=5)
        result = [
            {"text": seg.text.strip(), "start": seg.start, "end": seg.end}
            for seg in segments
            if seg.text and seg.text.strip()
        ]
        print(f"[INFO] Transcribed {Path(video_path).name}: "
              f"{len(result)} segments, language={info.language}")
        return result
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def group_segments_into_chunks(
    segments: List[Dict[str, Any]],
    max_chars: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Merge raw whisper segments (a few seconds each) into larger chunks
    (~max_chars long) while keeping the start/end timestamp of the merged
    range. Keeps retrieval granularity reasonable and keeps timestamps
    usable for "this is covered at 12:34" style answers.
    """
    chunks = []
    current_text = ""
    current_start = None
    current_end = None

    for seg in segments:
        if current_start is None:
            current_start = seg["start"]
        if len(current_text) + len(seg["text"]) > max_chars and current_text:
            chunks.append({"text": current_text.strip(), "start": current_start, "end": current_end})
            current_text = ""
            current_start = seg["start"]
        current_text += " " + seg["text"]
        current_end = seg["end"]

    if current_text.strip():
        chunks.append({"text": current_text.strip(), "start": current_start, "end": current_end})

    return chunks


def _format_timestamp(seconds: float) -> str:
    seconds = int(seconds or 0)
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def load_video_documents(data_dir: str, model_size: str = "base") -> List[Document]:
    """
    Walk data_dir for local video files, transcribe each one, and return
    Document objects ready to go through the existing chunk_documents /
    embed_chunks pipeline. Each Document already carries timestamp metadata
    for the chunk it represents.
    """
    data_path = Path(data_dir).resolve()
    video_files = [
        f for f in data_path.glob("**/*")
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
    print(f"[INFO] Found {len(video_files)} video files in {data_path}")

    documents = []
    for video_path in video_files:
        print(f"[INFO] Processing video: {video_path.name}")
        try:
            segments = transcribe_video(str(video_path), model_size=model_size)
            chunks = group_segments_into_chunks(segments)
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk["text"],
                    metadata={
                        "source": str(video_path),
                        "video_title": video_path.stem,
                        "type": "video",
                        "start_time": chunk["start"],
                        "end_time": chunk["end"],
                        "start_label": _format_timestamp(chunk["start"]),
                    }
                ))
        except Exception as e:
            print(f"[ERROR] Failed to process video {video_path.name}: {e}")

    print(f"[INFO] Total video document chunks created: {len(documents)}")
    return documents
