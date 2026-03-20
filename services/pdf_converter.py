import os, cloudconvert


class PDFConverter:
    def __init__(self, api_key):
        self.api_key = api_key
        cloudconvert.configure(api_key=api_key)
    
    def _find_task(self, job, operation):
        for t in job.get("tasks", []):
            if t.get("operation") == operation:
                return t
        return None
    
    # Job A: OCR (PDF -> OCR'ed PDF)
    def _ocr_pdf_job(self, pdf_path: str, languages=("eng",), auto_orient: bool = True):
        """
        Upload local PDF -> pdf/ocr -> export URL(s).
        Returns: list of exported file dicts, each with {"filename": "...", "url": "..."}.
        """
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "upload": {"operation": "import/upload"},
                "ocr": {
                    "operation": "pdf/ocr",
                    "input": "upload",
                    "language": list(languages),
                    "auto_orient": bool(auto_orient)
                },
                "export": {"operation": "export/url", "input": "ocr"}
            }
        })

        upload_task = self._find_task(job, "import/upload")
        if not upload_task:
            raise RuntimeError("No 'import/upload' task found in OCR job.")
        upload_task = cloudconvert.Task.find(id=upload_task["id"])
        cloudconvert.Task.upload(file_name=os.path.abspath(pdf_path), task=upload_task)

        export_task = self._find_task(job, "export/url")
        if not export_task:
            raise RuntimeError("No 'export/url' task found in OCR job.")
        export_task = cloudconvert.Task.wait(id=export_task["id"])

        files = (export_task.get("result") or {}).get("files") or []
        return files

    # Job B: PDF (OCR'ed) -> HTML
    def _pdf_to_html_job_from_url(self, pdf_url: str, out_dir: str, engine: str = "pdf2htmlex"):
        """
        Import OCR'ed PDF by URL -> convert (pdf->html) -> export URL(s) -> download HTML(s).
        Returns: list of local .html paths.
        """
        os.makedirs(out_dir, exist_ok=True)

        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-pdf": {
                    "operation": "import/url",
                    "url": pdf_url
                },
                "convert-pdf-html": {
                    "operation": "convert",
                    "input": "import-pdf",
                    "input_format": "pdf",
                    "output_format": "html",
                    "engine": engine,  # explicit engine for better academic layout
                    # You can add engine-specific options here if needed, e.g.:
                    # "embed_css": True,
                    # "split_pages": False,
                },
                "export-html": {
                    "operation": "export/url",
                    "input": "convert-pdf-html"
                }
            }
        })

        export_task = self._find_task(job, "export/url")
        if not export_task:
            raise RuntimeError("No 'export/url' task found in PDF->HTML job.")
        export_task = cloudconvert.Task.wait(id=export_task["id"])

        files = (export_task.get("result") or {}).get("files") or []
        html_paths = []
        for f in files:
            if not f["filename"].lower().endswith(".html"):
                # skip non-HTML assets, if any
                continue
            local_path = os.path.join(out_dir, f["filename"])
            cloudconvert.download(filename=local_path, url=f["url"])
            print(f"Downloaded file:{local_path} successfully..")
            html_paths.append(local_path)
        return html_paths

    # Job C: HTML -> TXT (local upload)
    def _html_local_to_txt_job(self, local_html_path: str, out_dir: str):
        """
        Import/upload local HTML -> convert (html->txt) -> export URL(s) -> download TXT(s).
        Returns: list of local .txt paths.
        """
        os.makedirs(out_dir, exist_ok=True)

        job = cloudconvert.Job.create(payload={
            "tasks": {
                "upload-html": {"operation": "import/upload"},
                "convert-html-txt": {
                    "operation": "convert",
                    "input": "upload-html",
                    "input_format": "html",
                    "output_format": "txt"
                },
                "export-txt": {
                    "operation": "export/url",
                    "input": "convert-html-txt"
                }
            }
        })

        upload_task = self._find_task(job, "import/upload")
        if not upload_task:
            raise RuntimeError("No 'import/upload' task in HTML->TXT job.")
        upload_task = cloudconvert.Task.find(id=upload_task["id"])
        cloudconvert.Task.upload(file_name=os.path.abspath(local_html_path), task=upload_task)

        export_task = self._find_task(job, "export/url")
        if not export_task:
            raise RuntimeError("No 'export/url' task in HTML->TXT job.")
        export_task = cloudconvert.Task.wait(id=export_task["id"])

        files = (export_task.get("result") or {}).get("files") or []
        txt_paths = []
        for f in files:
            if not f["filename"].lower().endswith(".txt"):
                continue
            local_path = os.path.join(out_dir, f["filename"])
            cloudconvert.download(filename=local_path, url=f["url"])
            print(f"Downloaded file:{local_path} successfully..")
            txt_paths.append(local_path)
        return txt_paths

    # Orchestrator: PDF -> OCR -> HTML -> TXT
    def convert_pdf_to_txt_with_ocr(self, pdf_path: str,
                                    out_dir: str,
                                    languages=("eng",),
                                    html_engine: str = "pdf2htmlex"):
        os.makedirs(out_dir, exist_ok=True)
        ocr_exports = self._ocr_pdf_job(pdf_path, languages=languages)
        if not ocr_exports:
            return []

        all_txt_paths = []
        for fpdf in ocr_exports:
            if not fpdf["filename"].lower().endswith(".pdf"):
                continue
            html_paths = self._pdf_to_html_job_from_url(fpdf["url"], out_dir, engine=html_engine)
            for hpath in html_paths:
                txt_paths = self._html_local_to_txt_job(hpath, out_dir)
                all_txt_paths.extend(txt_paths)

        return all_txt_paths
