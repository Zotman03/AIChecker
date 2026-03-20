# import streamlit as st

# st.title("🎈 My new app")
# st.write(
#     "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
# )

import streamlit as st
from txt_checker import run_txt_checker

st.title("🎈 My new app")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    # Save file locally
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("File uploaded!")

    if st.button("Run Checker"):
        result_path = run_txt_checker(uploaded_file.name)
        st.success("Processing complete!")

        # Show output
        with open(result_path, "r", encoding="utf-8") as f:
            html = f.read()

        st.components.v1.html(html, height=600, scrolling=True)