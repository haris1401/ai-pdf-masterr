import streamlit as st
from pypdf import PdfReader, PdfWriter
import io

st.set_page_config(page_title="PDF Tools", page_icon="📄", layout="wide")

st.title("📄 PDF Tools")
st.markdown("A simple tool to Merge, Rotate, and Extract Text from PDFs.")

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🔀 Merge PDFs", "🔄 Rotate Pages", "📝 Extract Text"])

# --- Tab 1: Merge PDFs ---
with tab1:
    st.header("Merge Multiple PDFs")
    uploaded_files = st.file_uploader("Upload PDFs to merge", type="pdf", accept_multiple_files=True, key="merge_upload")
    
    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} files.")
        
        if st.button("Merge PDFs"):
            if len(uploaded_files) < 2:
                st.warning("Please upload at least 2 PDF files to merge.")
            else:
                try:
                    merger = PdfWriter()
                    for pdf in uploaded_files:
                        merger.append(pdf)
                    
                    output_buffer = io.BytesIO()
                    merger.write(output_buffer)
                    merger.close()
                    
                    st.success("PDFs merged successfully!")
                    
                    st.download_button(
                        label="Download Merged PDF",
                        data=output_buffer.getvalue(),
                        file_name="merged_document.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# --- Tab 2: Rotate Pages ---
with tab2:
    st.header("Rotate PDF Pages")
    uploaded_rotate_file = st.file_uploader("Upload a PDF to rotate", type="pdf", key="rotate_upload")
    
    if uploaded_rotate_file:
        try:
            reader = PdfReader(uploaded_rotate_file)
            num_pages = len(reader.pages)
            st.info(f"This PDF has {num_pages} pages.")
            
            col1, col2 = st.columns(2)
            with col1:
                rotation_angle = st.selectbox("Rotation Angle (Clockwise)", [90, 180, 270], index=0)
            with col2:
                page_selection = st.radio("Apply rotation to:", ["All Pages", "Specific Pages"])
            
            pages_to_rotate = []
            if page_selection == "Specific Pages":
                page_input = st.text_input("Enter page numbers (comma separated, e.g., 1, 3, 5)", value="1")
                try:
                    # Convert 1-based user input to 0-based index
                    pages_to_rotate = [int(x.strip()) - 1 for x in page_input.split(",") if x.strip().isdigit()]
                except:
                    st.error("Invalid page number format.")
            else:
                pages_to_rotate = list(range(num_pages))
                
            if st.button("Rotate PDF"):
                writer = PdfWriter()
                
                for i in range(num_pages):
                    page = reader.pages[i]
                    if i in pages_to_rotate:
                        page.rotate(rotation_angle)
                    writer.add_page(page)
                
                output_buffer = io.BytesIO()
                writer.write(output_buffer)
                writer.close()
                
                st.success("PDF rotated successfully!")
                
                st.download_button(
                    label="Download Rotated PDF",
                    data=output_buffer.getvalue(),
                    file_name="rotated_document.pdf",
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

# --- Tab 3: Extract Text ---
with tab3:
    st.header("Extract Text from PDF")
    uploaded_text_file = st.file_uploader("Upload a PDF to extract text", type="pdf", key="text_upload")
    
    if uploaded_text_file:
        try:
            reader = PdfReader(uploaded_text_file)
            num_pages = len(reader.pages)
            
            st.info(f"Extracting text from {num_pages} pages...")
            
            full_text = ""
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += f"--- Page {i+1} ---\n{text}\n\n"
            
            if full_text:
                st.text_area("Extracted Text", full_text, height=400)
                st.download_button(
                    label="Download Text (.txt)",
                    data=full_text,
                    file_name="extracted_text.txt",
                    mime="text/plain"
                )
            else:
                st.warning("No text found. This might be a scanned PDF (image-based).")
                
        except Exception as e:
            st.error(f"Error extracting text: {e}")
