"""
Tutorial campaign progression helpers.

This module centralizes tutorial progression order and persistence.
To change progression order, edit TUTORIAL_PHASE_ORDER below.
"""

import json
import os
from typing import Dict, List, Set


# Change progression order here.
TUTORIAL_PHASE_ORDER: List[str] = [
    "Tutorial Modo Reto-Curva.png",
    "Mapa Tutorial Alertas de Inclinação.png",
    "Mapa Tutorial Alertas dos Sensores.png",
]

_PROGRESS_FILE_NAME = "tutorial_progress.json"

# Toggle persistence here:
# False -> progress resets every run (no file read/write)
# True  -> progress is saved/loaded from tutorial_progress.json
SAVE_TUTORIAL_PROGRESS = False

# In-memory session progress (always active for current process).
_SESSION_COMPLETED: Set[str] = set()


def _tutorial_dir(project_root: str) -> str:
    return os.path.join(project_root, "World", "Obstacles", "Tutorial")


def _progress_file_path(project_root: str) -> str:
    return os.path.join(_tutorial_dir(project_root), _PROGRESS_FILE_NAME)


def _load_progress(project_root: str) -> Dict[str, object]:
    if not SAVE_TUTORIAL_PROGRESS:
        return {"completed": []}

    path = _progress_file_path(project_root)
    if not os.path.isfile(path):
        return {"completed": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"completed": []}
        completed = data.get("completed", [])
        if not isinstance(completed, list):
            completed = []
        return {"completed": [str(name) for name in completed]}
    except Exception:
        return {"completed": []}


def _save_progress(project_root: str, completed: Set[str]) -> None:
    if not SAVE_TUTORIAL_PROGRESS:
        return

    tutorial_dir = _tutorial_dir(project_root)
    os.makedirs(tutorial_dir, exist_ok=True)

    path = _progress_file_path(project_root)
    data = {"completed": sorted(completed)}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_tutorial_maps(project_root: str) -> List[str]:
    tutorial_dir = _tutorial_dir(project_root)
    maps: List[str] = []

    for filename in TUTORIAL_PHASE_ORDER:
        full_path = os.path.join(tutorial_dir, filename)
        if os.path.isfile(full_path):
            maps.append(full_path)

    return maps


def get_tutorial_map_states(project_root: str) -> List[Dict[str, object]]:
    """Return ordered tutorial maps with sequential lock state."""
    tutorial_dir = _tutorial_dir(project_root)
    completed = get_completed_tutorial_levels(project_root)

    states: List[Dict[str, object]] = []
    all_previous_completed = True

    for filename in TUTORIAL_PHASE_ORDER:
        full_path = os.path.join(tutorial_dir, filename)
        if not os.path.isfile(full_path):
            continue

        is_completed = (filename in completed)
        is_unlocked = all_previous_completed

        states.append({
            "name": filename,
            "path": full_path,
            "unlocked": is_unlocked,
            "completed": is_completed,
        })

        if not is_completed:
            all_previous_completed = False

    return states


def get_completed_tutorial_levels(project_root: str) -> Set[str]:
    data = _load_progress(project_root)
    completed = {str(name) for name in data.get("completed", [])}
    return completed.union(_SESSION_COMPLETED)


def is_tutorial_map(project_root: str, map_path: str) -> bool:
    if not map_path:
        return False

    try:
        map_abs = os.path.abspath(map_path)
        tutorial_abs = os.path.abspath(_tutorial_dir(project_root))
        return map_abs.startswith(tutorial_abs)
    except Exception:
        return False


def get_next_tutorial_map(project_root: str) -> str:
    maps = get_tutorial_maps(project_root)
    if not maps:
        return ""

    completed = get_completed_tutorial_levels(project_root)

    # Sequential unlock: first non-completed phase in the ordered list.
    for map_path in maps:
        map_name = os.path.basename(map_path)
        if map_name not in completed:
            return map_path

    # All completed: fallback to last map in progression.
    return maps[-1]


def mark_tutorial_level_completed(project_root: str, map_path: str) -> bool:
    if not map_path:
        return False

    level_name = os.path.basename(map_path)
    completed = get_completed_tutorial_levels(project_root)
    was_already_completed = level_name in completed

    # Always update session memory so unlock works without file persistence.
    _SESSION_COMPLETED.add(level_name)

    if not was_already_completed:
        completed.add(level_name)
        _save_progress(project_root, completed)

    return (not was_already_completed)
