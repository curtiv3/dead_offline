"""
Generate an offline edit map from shot metadata without relying on external APIs.

Usage:
    python offline_director.py --shots shots.json --output edit_map.json --style horror_truecrime
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class Shot:
    start: float
    end: float
    avg_brightness: float
    motion: float

    @property
    def duration(self) -> float:
        return max(self.end - self.start, 0.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an offline edit map using heuristic rules.")
    parser.add_argument("--shots", required=True, help="Path to the shots JSON file")
    parser.add_argument("--output", required=True, help="Path for the edit map JSON file")
    parser.add_argument("--style", default="horror_truecrime", help="Style preset (horror_truecrime or analog_horror)")
    return parser.parse_args()


def load_shots(path: Path) -> List[Shot]:
    if not path.exists():
        raise FileNotFoundError(f"Shots file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    shots: List[Shot] = []
    for item in data:
        shots.append(
            Shot(
                start=float(item.get("start", 0.0)),
                end=float(item.get("end", 0.0)),
                avg_brightness=float(item.get("avg_brightness", 0.0)),
                motion=float(item.get("motion", 0.0)),
            )
        )
    return shots


def add_cut_for_long_shots(shot: Shot, events: List[dict], min_duration: float = 5.0) -> None:
    if shot.duration >= min_duration:
        midpoint = shot.start + shot.duration / 2.0
        events.append({"time": round(midpoint, 2), "action": "cut"})


def add_glitch_or_shake(shot: Shot, style: str, events: List[dict]) -> None:
    dark_and_chaotic = shot.avg_brightness < 0.3 and shot.motion > 0.6
    if not dark_and_chaotic:
        return

    if style == "analog_horror":
        events.append({"time": round(shot.start, 2), "action": "glitch", "duration": 0.4, "intensity": "high"})
    else:
        events.append({"time": round(shot.start, 2), "action": "shake", "duration": 0.3, "intensity": "medium"})


def add_flash_between_shots(prev_shot: Shot, current_shot: Shot, events: List[dict]) -> None:
    brightness_jump = current_shot.avg_brightness - prev_shot.avg_brightness
    if brightness_jump > 0.35:
        events.append({
            "time": round(current_shot.start, 2),
            "action": "flash",
            "color": "white",
            "duration": 0.2,
        })


def add_style_markers(shot: Shot, style: str, events: List[dict]) -> None:
    if style == "horror_truecrime" and shot.avg_brightness < 0.35 and shot.motion < 0.4:
        events.append({"time": round(shot.start, 2), "action": "marker", "label": "tension_point"})
    if style == "analog_horror" and shot.motion > 0.5 and shot.avg_brightness < 0.5:
        events.append({"time": round(shot.start + min(shot.duration * 0.7, 0.5), 2), "action": "marker", "label": "desync"})


def add_periodic_markers(shots: Iterable[Shot], events: List[dict], interval: float = 10.0) -> None:
    next_marker = interval
    for shot in shots:
        while shot.start <= next_marker < shot.end:
            events.append({"time": round(next_marker, 2), "action": "marker", "label": "beat"})
            next_marker += interval


def generate_edit_map(shots: List[Shot], style: str) -> List[dict]:
    events: List[dict] = []
    if not shots:
        return events

    for idx, shot in enumerate(shots):
        add_cut_for_long_shots(shot, events)
        add_glitch_or_shake(shot, style, events)
        add_style_markers(shot, style, events)

        if idx > 0:
            add_flash_between_shots(shots[idx - 1], shot, events)

    add_periodic_markers(shots, events)
    events.sort(key=lambda item: item.get("time", 0.0))
    return events


def write_output(edit_map: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(edit_map, fh, indent=2)


def main() -> None:
    args = parse_args()
    shots_path = Path(args.shots)
    output_path = Path(args.output)

    try:
        shots = load_shots(shots_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not shots:
        print("No shots available; generated an empty edit map.", file=sys.stderr)
        write_output([], output_path)
        sys.exit(0)

    edit_map = generate_edit_map(shots, args.style)
    write_output(edit_map, output_path)
    print(f"Generated {len(edit_map)} edit events to {output_path}")


if __name__ == "__main__":
    main()
