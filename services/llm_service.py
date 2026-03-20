from openai import OpenAI

class LLMService:
    def __init__(self, api_key, model="gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def extract_title_from_reference(self, ref_line: str):
        """
        Given a single reference line, use GPT to extract the paper title only.
        Returns the title string or None if not found.
        """
        try:
            system_prompt = (
                "You are a reference text analyzer.\n"
                "Input: one bibliographic reference line.\n"
                "Output: ONLY the first author's lastname and title of the paper, exactly as it appears.\n"
                "Do not include other authors, journal names, or DOIs.\n"
                "If the title cannot be found, return 'None'.\n"
                "Return in the format of 'LASTNAME, Title'.\n"
                "Do not make up or autocomplete any doi or title, you can only infer from the existing lines.\n"
                "Do not add any extra explanation."
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ref_line}
                ]
            )

            title = response.choices[0].message.content.strip().strip('"').strip()
            if title.lower() in ("none", ""):
                return None
            return title

        except Exception as e:
            return None
    
    def openai_response(self, prompt):
        try:
            system_prompt = """You are a text-processing assistant. 
                You will receive the full content of a `.txt` file that contains many references or citations. 
                Some citations may be broken across multiple lines (for example, when a reference wraps between pages). 
                Your task is to reconstruct each citation so that each full reference appears on exactly ONE line.

                Follow these rules carefully:
                1. Combine consecutive lines that belong to the same citation into a single line.
                2. Keep the original punctuation, spacing, and wording from the source text.
                3. Insert a single space where line breaks were removed (unless there is already a space).
                4. Ensure each complete citation ends with a period, and there is exactly one blank line between citations.
                5. Do not merge two different citations together — start a new line when a new citation begins (often identified by a new author name pattern like "Lastname, Initial." or a year like "2020:").
                6. Output plain text only, with one reference per line.
                7. Start with (<GPT I will start>) at a separate line. When finished, put (<GPT I am done>) at the end in a separate line.
                8. If you saw anything that is a header or a footer, ignore it. For example, page numbers, or repetitive doi with page number and author etc. But if the header and footer are within another reference, just remove the header and footer, keep the rest of the reference as is.

                Example Input:
                Aðalgeirsdóttir, G. et al., 2020: Glacier changes in Iceland from ~1890 to 2019.  
                Frontiers in Earth Science, 8, 520, doi:10.3389/feart.2020.523646.  
                Adler,  R.F.  et  al.,  2003:  The  Version-2  Global  Precipitation  Climatology  
                Project  (GPCP)  Monthly  Precipitation  Analysis  (1979-Present).  Journal  
                of  Hydrometeorology,  4(6),  1147-1167,  doi:10.1175/1525-7541(2003)  
                004<1147:tvgpcp>2.0.co;2.  
                Adusumilli, S., H.A. Fricker, B. Medley, L. Padman, and M.R. Siegfried, 2020:  
                Interannual  variations  in  meltwater  input  to  the  Southern  Ocean  from  
                Antarctic  ice  shelves.  Nature  Geoscience,  13,  616-620,  doi:10.1038/  
                s41561-020-0616-z.
                Park, B., Pit
                ˇ
                na, A., Šafránková, J., N
                ˇ
                eme
                ˇ
                cek, Z., Krupa
                ˇ
                rová,
                O., Krupa
                ˇ
                r, V., Zhao, L., and Silwal, A.: Change of Spec-
                tral Properties of Magnetic Field Fluctuations across Differ-
                Ann. Geophys., 43, 489-510, 2025 https://doi.org/10.5194/angeo-43-489-2025
                10.1086/146579,
                10.1016/S0273-1177(03)90635-
                16-017-001
                1-z,
                2018.
                E. Kilpua et al.: Shock effect on turbulence parameters 509
                ent Types of Interplanetary Shocks, Astrophys. J., 954, L51,
                https://doi.org/10.3847/2041-8213/acf4ff, 2023.

                Example Output:
                (<GPT I will start>)
                Aðalgeirsdóttir, G. et al., 2020: Glacier changes in Iceland from ~1890 to 2019. Frontiers in Earth Science, 8, 520, doi:10.3389/feart.2020.523646.

                Adler, R.F. et al., 2003: The Version-2 Global Precipitation Climatology Project (GPCP) Monthly Precipitation Analysis (1979-Present). Journal of Hydrometeorology, 4(6), 1147-1167, doi:10.1175/1525-7541(2003)004<1147:tvgpcp>2.0.co;2.

                Adusumilli, S., H.A. Fricker, B. Medley, L. Padman, and M.R. Siegfried, 2020: Interannual variations in meltwater input to the Southern Ocean from Antarctic ice shelves. Nature Geoscience, 13, 616-620, doi:10.1038/s41561-020-0616-z.

                Park, B., Pitˇ na, A., Šafránková, J., Nˇemeˇ cek, Z., Krupaˇ rová,O., Krupaˇ r, V., Zhao, L., and Silwal, A.: Change of Spectral Properties of Magnetic Field Fluctuations across Different Types of Interplanetary Shocks, Astrophys. J., 954, L51, https://doi.org/10.3847/2041-8213/acf4ff, 2023.
                (<GPT I am done>)
                """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"ERROR: {str(e)}"