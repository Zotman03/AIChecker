from pathlib import Path

from models import ReportData


class ReferenceCheckerService:
    def __init__(self, config, pdf_converter, llm_service, reference_service, report_builder):
        self.config = config
        self.pdf_converter = pdf_converter
        self.llm_service = llm_service
        self.reference_service = reference_service
        self.report_builder = report_builder

    def run(self, pdf_path: str) -> ReportData:
        self.config.ensure_directories()

        file_stem = Path(pdf_path).stem

        txt_paths = self.pdf_converter.convert_pdf_to_txt_with_ocr(
            pdf_path=pdf_path,
            out_dir=str(self.config.paper_txt_dir),
        )
        if not txt_paths:
            raise RuntimeError("No TXT file was generated from the PDF conversion.")

        txt_path = Path(txt_paths[0])
        txt = txt_path.read_text(encoding="utf-8", errors="ignore")

        messy_block = self.reference_service.get_references_block(txt)
        messy_path = self.config.messy_txt_dir / f"{file_stem}_reference.txt"
        messy_path.write_text(messy_block, encoding="utf-8")

        cleaned_text = self.llm_service.openai_response(messy_block)
        clean_path = self.config.clean_txt_dir / f"{file_stem}_reference.txt"
        clean_path.write_text(cleaned_text, encoding="utf-8")

        references = self.reference_service.extract_cleaned_references(cleaned_text)
        result = self.reference_service.process_references_with_doi(references)
        result.suggested_dois = self.reference_service.suggest_dois_for_missing(
            result.no_doi_references,
            self.llm_service,
        )

        html = self.report_builder.build(
            result=result
        )

        report_path = self.config.report_dir / f"{file_stem}_report.html"
        report_path.write_text(html, encoding="utf-8")

        return ReportData(
            file_stem=file_stem,
            report_path=report_path,
            html_content=html,
        )