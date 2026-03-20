from models import ReferenceValidationResult


class HtmlReportBuilder:
    def __init__(self, reference_service):
        self.reference_service = reference_service

    def build(self, result: ReferenceValidationResult) -> str:
        html_parts = [
            """
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reference Validation Report</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 24px; }
                    .section { margin-bottom: 32px; }
                    a { color: #0066cc; text-decoration: underline; }
                    a:hover { color: #004499; }
                    li { margin-bottom: 12px; }
                </style>
            </head>
            <body>
            """
        ]

        html_parts.append(f'<div class="section"><h1>Wrong DOI List ({len(result.wrong_doi_list)})</h1><ul>')
        for ref in result.wrong_doi_list:
            clickable_ref = self.reference_service.make_doi_clickable(ref)
            reason = result.reason_list.get(ref, "")
            html_parts.append(f'<li><b>{clickable_ref}</b><br><em>Reason:</em> {reason}</li>')
        html_parts.append("</ul></div>")

        html_parts.append(f'<div class="section"><h1>No DOI References ({len(result.no_doi_references)})</h1><ul>')
        for ref in result.no_doi_references:
            possible_dois = result.suggested_dois.get(ref, [])
            rendered_ref = ref
            if possible_dois:
                doi_links = [
                    self.reference_service.make_doi_clickable(f"doi:{doi}", flag=False)
                    for doi in possible_dois
                ]
                rendered_ref += "<br>Possible DOIs: " + " |||| ".join(doi_links) + "<br><br>"
            html_parts.append(f"<li>{rendered_ref}</li>")
        html_parts.append("</ul></div>")

        html_parts.append(f'<div class="section"><h1>Valid References ({len(result.valid_references)})</h1><ul>')
        for ref in result.valid_references:
            clickable_ref = self.reference_service.make_doi_clickable(ref)
            html_parts.append(f"<li>{clickable_ref}</li>")
        html_parts.append("</ul></div>")

        html_parts.append("</body></html>")
        return "".join(html_parts)