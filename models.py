from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ReferenceValidationResult:
    valid_references: list
    wrong_doi_list: list
    no_doi_references: list
    reason_list: dict
    suggested_dois: dict[str, list[str]] = field(default_factory=dict)

@dataclass
class ReportData:
    file_stem: str
    report_path: Path
    html_content: str