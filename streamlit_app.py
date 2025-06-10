import streamlit as st
from standalone import parse_markdown_slides, render_slide_html, TEMPLATE_HEAD, TEMPLATE_FOOT, TEMPLATE_SCRIPT
import markdown

st.title("Markdown to Presentation Converter")
uploaded_md = st.file_uploader("Upload your Markdown (.md) file", type=["md"])

if uploaded_md:
    md_text = uploaded_md.read().decode("utf-8")
    slides = parse_markdown_slides(md_text)
    slides_html = "\n".join(render_slide_html(s, i) for i, s in enumerate(slides))

    full_html = TEMPLATE_HEAD + slides_html + TEMPLATE_FOOT + ''.join(
        f'<button class="btn btn-outline-dark pagination-btn mx-1" data-index="{i}">{i+1}</button>' for i in range(len(slides))
    ) + """
        <div class="d-flex justify-content-center mb-5">
          <button class="btn btn-success mx-2" id="export-pdf">Export PDF</button>
          <button class="btn btn-success mx-2" id="export-png">Export PNGs</button>
        </div>
    """ + TEMPLATE_SCRIPT

    st.download_button("Download HTML Presentation", full_html, file_name="presentation.html", mime="text/html")
    st.components.v1.html(full_html, height=800, scrolling=True)
