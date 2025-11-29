"""
Stub for applying an edit map to DaVinci Resolve by placing markers on the timeline.

Run this inside the DaVinci Resolve scripting console. The script reads an
`edit_map.json` file and converts events into colored markers so further effects
can be added manually.
"""
from __future__ import annotations

import json
from pathlib import Path

from python_get_resolve import GetResolve


ACTION_COLORS = {
    "glitch": "Red",
    "shake": "Red",
    "flash": "Yellow",
    "cut": "Green",
    "marker": "Blue",
}


def seconds_to_frame(seconds: float, fps: float) -> int:
    return int(round(seconds * fps))


def load_edit_map(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    edit_path = Path(input("Path to edit_map.json: ").strip() or "edit_map.json")
    events = load_edit_map(edit_path)

    resolve = GetResolve()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    if project is None:
        print("No active project found.")
        return

    timeline = project.GetCurrentTimeline()
    if timeline is None:
        print("No active timeline found.")
        return

    fps = float(timeline.GetSetting("timelineFrameRate") or 24.0)

    for event in events:
        seconds = float(event.get("time", 0.0))
        action = event.get("action", "marker")
        label = event.get("label", action)
        color = ACTION_COLORS.get(action, "Blue")
        frame_id = seconds_to_frame(seconds, fps)
        timeline.AddMarker(frame_id, color, label, str(event))

    print(f"Applied {len(events)} markers from {edit_path}")


if __name__ == "__main__":
    main()
