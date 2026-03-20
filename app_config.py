from dataclasses import dataclass
from pathlib import Path

@dataclass
class AppConfig:
    uploads_dir: Path = Path("uploads")
    paper_txt_dir: Path = Path("paper_txt")
    messy_txt_dir: Path = Path("reference_messy_txt")
    clean_txt_dir: Path = Path("reference_clean_txt")
    report_dir: Path = Path("html_report")

    def ensure_directories(self):
        for directory in [self.uploads_dir, self.paper_txt_dir, self.messy_txt_dir, self.clean_txt_dir, self.report_dir]:
            directory.mkdir(parents=True, exist_ok=True)