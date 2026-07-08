"""Chapter progress tracking using local JSON storage."""
import os
import json
from datetime import datetime

PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '.omo', 'progress.json')

def _ensure_dir():
    d = os.path.dirname(PROGRESS_FILE)
    if not os.path.exists(d):
        os.makedirs(d)

def load_progress():
    _ensure_dir()
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_progress(progress):
    _ensure_dir()
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

def mark_visited(chapter_num, chapter_name):
    progress = load_progress()
    key = str(chapter_num)
    if key not in progress:
        progress[key] = {
            "name": chapter_name,
            "first_visit": datetime.now().isoformat(),
            "visit_count": 1
        }
    else:
        progress[key]["visit_count"] = progress[key].get("visit_count", 0) + 1
    progress[key]["last_visit"] = datetime.now().isoformat()
    save_progress(progress)

def get_progress_summary(total_chapters):
    progress = load_progress()
    visited = len(progress)
    percentage = int(visited / total_chapters * 100) if total_chapters > 0 else 0
    return visited, total_chapters, percentage

def is_chapter_visited(chapter_num):
    progress = load_progress()
    return str(chapter_num) in progress
