import os
import streamlit as st

from app_config import AppConfig
from report.html_report_builder import HtmlReportBuilder
from services.checker_service import ReferenceCheckerService
from services.llm_service import LLMService
from services.pdf_converter import PDFConverter
from services.reference_service import ReferenceService

st.set_page_config(page_title="Detect AI Hallucination", page_icon="📄", layout="centered")

config = AppConfig()

reference_service = ReferenceService()

report_builder = HtmlReportBuilder(reference_service=reference_service)

checker = ReferenceCheckerService(
    config=config,
    pdf_converter=PDFConverter(api_key=st.secrets["C_KEY"]),
    llm_service=LLMService(api_key=st.secrets["OPENAI_API_KEY"]),
    reference_service=reference_service,
    report_builder=report_builder,
)

st.title("Detect AI Hallucination 📄")
st.write("Upload a PDF to validate references and detect potential AI-generated errors")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    config.ensure_directories()
    saved_path = config.uploads_dir / uploaded_file.name
    with open(saved_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("File uploaded successfully.")

    if st.button("Run Checker"):
        with st.spinner("Processing file..."):
            artifact = checker.run(str(saved_path))

        st.success("Processing complete.")
        st.components.v1.html(artifact.html_content, height=650, scrolling=True)
        st.download_button(
            "Download HTML Report",
            data=artifact.html_content,
            file_name=f"{artifact.file_stem}_report.html",
            mime="text/html",
        )
# python -m streamlit run streamlit_app.py
