"""
Analyze a video to detect shots and basic metadata such as brightness and motion.

Usage:
    python analyze_video.py --input input.mp4 --output shots.json

The script uses a simple histogram difference for shot detection and tracks
brightness and frame-to-frame motion within each shot.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np


@dataclass
class ShotMetrics:
    start_frame: int
    end_frame: int
    fps: float
    brightness_sum: float = 0.0
    motion_sum: float = 0.0
    frames: int = 0

    @property
    def start(self) -> float:
        return self.start_frame / self.fps if self.fps else 0.0

    @property
    def end(self) -> float:
        return self.end_frame / self.fps if self.fps else 0.0

    def to_dict(self) -> dict:
        frames_safe = max(self.frames, 1)
        avg_brightness = self.brightness_sum / frames_safe
        motion = self.motion_sum / frames_safe
        return {
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "avg_brightness": round(float(avg_brightness), 3),
            "motion": round(float(min(motion, 1.0)), 3),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect shots and simple metadata from a video file.")
    parser.add_argument("--input", required=True, help="Path to the input video file")
    parser.add_argument("--output", required=True, help="Path for the output JSON file")
    parser.add_argument("--threshold", type=float, default=0.45, help="Shot change threshold (histogram distance)")
    parser.add_argument(
        "--min-shot-duration",
        type=float,
        default=0.5,
        help="Minimum shot duration in seconds to avoid tiny segments",
    )
    return parser.parse_args()


def ensure_video(path: Path) -> cv2.VideoCapture:
    if not path.exists():
        raise FileNotFoundError(f"Input video not found: {path}")
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    return cap


def histogram_distance(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    hist_size = 32
    hist_range = [0, 256]
    hist_a = cv2.calcHist([frame_a], [0], None, [hist_size], hist_range)
    hist_b = cv2.calcHist([frame_b], [0], None, [hist_size], hist_range)
    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)
    score = cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
    return float(1.0 - score)


def detect_shots(cap: cv2.VideoCapture, fps: float, threshold: float, min_shot_frames: int) -> List[ShotMetrics]:
    shots: List[ShotMetrics] = []
    ret, prev_frame = cap.read()
    if not ret:
        return shots

    frame_index = 0
    gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    current_shot = ShotMetrics(start_frame=0, end_frame=0, fps=fps)
    current_shot.brightness_sum = gray_prev.mean() / 255.0
    current_shot.motion_sum = 0.0
    current_shot.frames = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_index += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Update metrics for current shot
        brightness = gray.mean() / 255.0
        diff = cv2.absdiff(gray, gray_prev)
        motion = float(diff.mean() / 255.0)
        current_shot.brightness_sum += brightness
        current_shot.motion_sum += motion
        current_shot.frames += 1

        # Detect potential cut
        distance = histogram_distance(gray, gray_prev)
        if distance > threshold and current_shot.frames >= min_shot_frames:
            current_shot.end_frame = frame_index
            shots.append(current_shot)
            current_shot = ShotMetrics(start_frame=frame_index, end_frame=frame_index, fps=fps)

        gray_prev = gray

    # finalize last shot
    current_shot.end_frame = frame_index + 1
    shots.append(current_shot)
    return shots


def write_output(shots: List[ShotMetrics], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump([shot.to_dict() for shot in shots], fh, indent=2)


def main() -> None:
    args = parse_args()
    video_path = Path(args.input)
    output_path = Path(args.output)

    try:
        cap = ensure_video(video_path)
    except (FileNotFoundError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    min_shot_frames = max(int(fps * args.min_shot_duration), 1)

    shots = detect_shots(cap, fps, threshold=args.threshold, min_shot_frames=min_shot_frames)
    cap.release()

    if not shots:
        print("No frames detected; no shots generated.", file=sys.stderr)
        sys.exit(1)

    write_output(shots, output_path)
    print(f"Wrote {len(shots)} shots to {output_path}")


if __name__ == "__main__":
    main()
