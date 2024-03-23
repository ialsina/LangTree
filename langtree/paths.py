from pathlib import Path
from dataclasses import dataclass

ROOT_DIR = Path(__file__).absolute().parent.parent
DATA_DIR = ROOT_DIR / "data"
HTML_DIR = DATA_DIR / "html"

@dataclass
class paths:
    manual_nodes      = DATA_DIR / "manual_nodes.txt"
    comparison_report = DATA_DIR / "comparison_report.txt"
    lang_iso_name     = DATA_DIR / "lang_iso_name.json"
    language_speakers = DATA_DIR / "language_speakers.txt"
    families          = DATA_DIR / "families.txt"
