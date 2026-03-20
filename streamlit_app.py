import os
import streamlit as st
from txt_checker import run_txt_checker

st.set_page_config(
    page_title="Detect AI Hallucination",
    page_icon="📄",
    layout="centered",
)

os.makedirs("uploads", exist_ok=True)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #6b8cff 0%, #7a5bd6 100%);
    }

    .main > div {
        max-width: 900px;
        padding-top: 2rem;
    }

    .title-wrap {
        text-align: center;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        color: white;
    }

    .title-wrap h1 {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }

    .title-wrap p {
        font-size: 1.15rem;
        opacity: 0.95;
        margin-top: 0;
    }

    .upload-card {
        background: #f7f7f8;
        border-radius: 24px;
        padding: 2.5rem 2rem;
        box-shadow: 0 18px 45px rgba(40, 20, 90, 0.22);
        margin: 1.5rem auto 2rem auto;
    }

    /* File uploader container */
    [data-testid="stFileUploader"] {
        background: transparent;
        border: none;
        padding: 0;
    }

    [data-testid="stFileUploader"] section {
        border: 2px dashed #d6d6df;
        border-radius: 20px;
        background: #ffffff;
        min-height: 320px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: white !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] {
        text-align: center;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] div {
        font-size: 1.1rem;
        color: #444;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #777 !important;
    }

    /* Hide default small uploader label */
    .stFileUploader label {
        display: none;
    }

    /* Buttons */
    .stButton > button,
    [data-testid="stFileUploader"] button {
        background: linear-gradient(90deg, #6f7cff 0%, #8e4fd8 100%);
        color: white;
        border: none;
        border-radius: 999px;
        padding: 0.7rem 1.8rem;
        font-size: 1rem;
        font-weight: 600;
        box-shadow: 0 8px 20px rgba(101, 86, 214, 0.35);
    }

    .stButton > button:hover,
    [data-testid="stFileUploader"] button:hover {
        color: white;
        opacity: 0.96;
    }

    .report-box {
        background: white;
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 10px 30px rgba(40, 20, 90, 0.18);
        margin-top: 1rem;
        margin-bottom: 2rem;
    }

    .download-wrap {
        margin-top: 1rem;
        text-align: center;
    }

    /* Success/info messages */
    [data-testid="stAlert"] {
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="title-wrap">
        <h1>Detect AI Hallucination 📄</h1>
        <p>Upload a PDF to validate references and detect potential AI-generated errors</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")

st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file:
    saved_path = os.path.join("uploads", uploaded_file.name)

    with open(saved_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("File uploaded successfully.")

    if st.button("Run Checker"):
        with st.spinner("Processing file..."):
            result_path = run_txt_checker(saved_path)

        st.success("Processing complete.")

        with open(result_path, "r", encoding="utf-8") as f:
            html = f.read()

        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.subheader("Report Preview")
        st.components.v1.html(html, height=650, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="download-wrap">', unsafe_allow_html=True)
        st.download_button(
            label="Download HTML Report",
            data=html,
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_report.html",
            mime="text/html",
        )
        st.markdown("</div>", unsafe_allow_html=True)
