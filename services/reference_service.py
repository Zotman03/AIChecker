import re
import requests
import unicodedata
import urllib.parse

from models import ReferenceValidationResult

UNICODE_DASHES = "‐–—−"
UNICODE_LANGLE = ["〈", "〈", "﹤", "＜"]  # U+2329, U+3008, etc.
UNICODE_RANGLE = ["〉", "〉", "﹥", "＞"]  # U+232A, U+3009, etc.

class ReferenceService:
    def __init__(self):
        pass

    def normalize_reference_text(self, text):
        text = text.replace("‐", "-").replace("–", "-").replace("—", "-").replace("−", "-")
        normalized = re.sub(r'(\w)/\s+(\w)', r'\1/\2', text)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def get_references_block(self, text):
        """
        Extract ref / bib from a txt file. Start with header, then end before appendix etc
        """
        t = text.replace('\r\n', '\n').replace('\r', '\n')

        # Header: references / reference / bibliography (colon/dashes optional), alone on line
        start_pat = re.compile(
            r'^[ \t]*(?:references?|bibliography)[ \t]*:?[ \t]*[-–—=]*[ \t]*$',
            re.IGNORECASE | re.MULTILINE
        )
        m_start = start_pat.search(t)
        if not m_start:
            return ""

        # Enders: next major section headers after references
        end_pat = re.compile(
            r'^[ \t]*(?:'
            r'appendix(?:\s+[A-Z0-9]+)?|appendices|'
            r'supplementary(?:\s+material)?|supplemental|'
            r'figures?|tables?'
            r')[ \t]*[:\-–—=]?\b.*$',
            re.IGNORECASE | re.MULTILINE
        )
        m_end = end_pat.search(t, pos=m_start.end())

        start_idx = m_start.end()
        end_idx = m_end.start() if m_end else len(t)

        block = t[start_idx:end_idx].strip()
        cleaned_lines = []
        for line in block.split('\n'):
            s = line.strip()
            if not s:
                continue
            if re.fullmatch(r'\d+', s):
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()
    
    def extract_cleaned_references(self, cleaned_text: str) -> list[str]:
        match = re.search(r'\(<GPT I will start>\)(.*?)\(<GPT I am done>\)', cleaned_text, re.DOTALL)
        relevant_text = match.group(1).strip() if match else cleaned_text.strip()
        return [line.strip() for line in relevant_text.split("\n") if line.strip()]


    def extract_doi_from_text(self, text):
        t = unicodedata.normalize("NFKC", text)
        for ch in UNICODE_DASHES: t = t.replace(ch, "-")
        for ch in UNICODE_LANGLE: t = t.replace(ch, "<")
        for ch in UNICODE_RANGLE: t = t.replace(ch, ">")
        doi_patterns = [
            r'doi:\s*10\.\d{4,9}/[-._;()/:<>#a-zA-Z0-9]+',
            r'https?://doi\.org/10\.\d{4,9}/[-._;()/:<>#a-zA-Z0-9]+',
            r'doi.org/10\.\d{4,9}/[-._;()/:<>#a-zA-Z0-9]+',
        ]
        
        normalized_text = self.normalize_reference_text(t)
        
        for pattern in doi_patterns:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                doi_match = match.group(0)
                if doi_match.startswith('doi:'):
                    doi = doi_match[4:]
                elif 'doi.org/' in doi_match:
                    doi = doi_match.split('doi.org/')[-1]
                elif '://' in doi_match:
                    doi = doi_match.split('/')[-1]
                else:
                    doi = doi_match

                if doi.endswith('.'):
                    doi = doi[:-1]
                
                return doi
        return None
    
    def get_doi_data(self,doi):
        url = "https://citation.doi.org/metadata"
        params = {"doi": doi}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            title = data.get("title", "N/A")
            if isinstance(title, list):
                title = title[0] if title else "N/A"
            title = title.replace("‐", "-")
            title = title.replace("–", "-")
            #title = title.replace("-", "")
            title = title.replace("’", "'")
            title = re.sub(r"[?!]", "", title)
            title = re.sub(r"\s+", " ", title).strip()
            
            authors = data.get("author", [])
            author_names = []
            if not authors:
                return title, None
            
            for author in authors:
                last = author.get("family", "")
                last = last.replace("’", "'")
                author_names.append(f"{last}".strip())
            
            first_author_last_name = author_names[0] if author_names else None
            return title, first_author_last_name

        except requests.RequestException as e:
            return None, None
    
    def is_text_in_reference(self,search_text, reference_text):
        """
        Check if search_text appears in reference_text (case-insensitive, partial matching)
        """
        if not search_text or search_text == 'N/A':
            return False
        
        def normalize_text(text):
            if not text:
                return ""
            text = unicodedata.normalize('NFKC', text)
            text = text.replace("‐", "-").replace("–", "-").replace("—", "-").replace("−", "-")
            
            # Remove punctuation and normalize whitespace
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            
            return text.lower().strip()
        
        clean_search = normalize_text(search_text.lower())
        clean_ref = normalize_text(reference_text.lower())
        
        search_words = [word for word in clean_search.split() if len(word) > 3]
        
        if not search_words:
            return False
        
        matches = sum(1 for word in search_words if word in clean_ref)
        
        # Return True if at least 70% of significant words match
        return matches / len(search_words) >= 0.7
    
    def process_references_with_doi(self,references):
        no_doi_references = []
        valid_references = []
        wrong_doi_list = []
        reason_list = dict()
        
        for ref in references:
            doi = self.extract_doi_from_text(ref)
            if doi:
                title, first_author = self.get_doi_data(doi)
                if title is None and first_author is None:
                    wrong_doi_list.append(ref)
                    reason_list[ref] = "DOI and author not found in doi.org, likely invalid DOI"
                else:
                    title_in_ref = self.is_text_in_reference(title, ref)
                    if not title_in_ref:
                        wrong_doi_list.append(ref)
                        reason_list[ref] = "Title mismatch in reference"
                        continue
                    
                    valid_references.append(ref)
            else:
                no_doi_references.append(ref)
        
        return ReferenceValidationResult(valid_references, wrong_doi_list, no_doi_references, reason_list)
    
    def query_crossref_by_title(self, title: str, author: str) -> list[dict]:
        q = urllib.parse.quote(title)
        a = urllib.parse.quote(author)
        url = f"https://api.crossref.org/works?query.title={q}&query.author={a}&rows={3}"
        headers = {"User-Agent": "DOI-Finder/1.0 (mailto:your.email@example.com)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        items = response.json()["message"]["items"]

        results = []
        for item in items:
            results.append({
                "title": item.get("title", [""])[0],
                "doi": item.get("DOI"),
                "year": item.get("issued", {}).get("date-parts", [[None]])[0][0],
                "publisher": item.get("publisher"),
                "authors": [
                    f"{author.get('given', '')} {author.get('family', '')}".strip()
                    for author in item.get("author", [])
                    if f"{author.get('given', '')} {author.get('family', '')}".strip()
                ],
            })
        return results

    def suggest_dois_for_missing(self, refs_without_doi: list[str], llm_service) -> dict[str, list[str]]:
        suggestions = {}
        for ref in refs_without_doi:
            result = llm_service.extract_title_from_reference(ref)
            if not result or "," not in result:
                continue
            author, title = result.split(",", 1)
            papers = self.query_crossref_by_title(title.strip(), author.strip())
            suggestions[ref] = [paper["doi"] for paper in papers if paper.get("doi")]
        return suggestions
    
    def make_doi_clickable(self, ref_text: str, flag: bool = True) -> str:
        ref_text = ref_text.replace("‐", "-").replace("–", "-").replace("—", "-").replace("−", "-")
        ref_text = ref_text.replace("<", "&lt;").replace(">", "&gt;")

        doi = self.extract_doi_from_text(ref_text) if flag else ref_text
        if not doi:
            return ref_text

        doi = doi.replace("‐", "-").replace("–", "-").replace("—", "-").replace("−", "-")
        doi_url = f"https://doi.org/{doi}"

        doi_patterns = [
            (r'https?://doi\.org/10\.\d{4,9}/[^\s"\'<>]+', lambda m: f'<a href="{doi_url}" target="_blank">{m.group(0)}</a>'),
            (r'doi:\s*10\.\d{4,9}/[^\s"\'<>]+', lambda m: f'<a href="{doi_url}" target="_blank">{m.group(0)}</a>'),
            (r'doi\.org/10\.\d{4,9}/[^\s"\'<>]+', lambda m: f'<a href="{doi_url}" target="_blank">{m.group(0)}</a>'),
        ]

        for pattern, replacement in doi_patterns:
            if re.search(pattern, ref_text, re.IGNORECASE):
                return re.sub(pattern, replacement, ref_text, count=1, flags=re.IGNORECASE)

        return ref_text