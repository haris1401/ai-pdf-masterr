import streamlit as st
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import io
import re
import os
import openai
from dotenv import load_dotenv

# Load environment variables (for OpenAI key if present)
load_dotenv()
if os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI PDF Master", page_icon="🤖", layout="wide")

st.title("🤖 AI PDF Master: Smart PDF Editor")
st.markdown("Edit PDFs by simply **typing instructions**. E.g., *'Change the date to 2025'*, *'Replace John with Jane'*.")

# --- Sidebar ---
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    st.divider()
    st.info("**AI Status**")
    if os.getenv("OPENAI_API_KEY"):
        st.success("OpenAI Key Detected! ✅")
    else:
        st.warning("No OpenAI Key found. Using rule-based logic only.")
        api_key_input = st.text_input("Enter OpenAI API Key (Optional)", type="password")
        if api_key_input:
            openai.api_key = api_key_input
            st.success("Key set for this session!")

if not uploaded_file:
    st.info("Please upload a PDF to get started.")
    st.stop()

# Load PDF with PyMuPDF
doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

# Tabs
tab_magic, tab_manual, tab_extract, tab_ai = st.tabs(["✨ Magic Edit", "✏️ Manual Edit", "📊 Analyzer", "🤖 AI Chat"])

# Helper function to process natural language command with LLM
def parse_edit_command(command_text):
    """
    Uses OpenAI to extract 'find_text' and 'replace_text' from natural language.
    """
    if not openai.api_key:
        return None, None, "OpenAI API Key required for smart parsing."
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a command parser. Extract the 'find' text and 'replace' text from the user's edit instruction. Return ONLY a JSON object: {\"find\": \"...\", \"replace\": \"...\"}. If the user says 'delete X', replace should be empty string. Example: 'Change 2023 to 2024' -> {\"find\": \"2023\", \"replace\": \"2024\"}"},
                {"role": "user", "content": command_text}
            ]
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get("find"), result.get("replace"), None
    except Exception as e:
        return None, None, str(e)

# ==========================================
# TAB 1: MAGIC EDIT (Natural Language)
# ==========================================
with tab_magic:
    st.header("✨ Magic Editor")
    st.write("Tell the AI what to change in the PDF.")
    
    edit_instruction = st.text_area("What should I change?", placeholder="e.g., Replace 'Invoice #001' with 'Invoice #999', or change 'Due Date: Jan 1' to 'Due Date: Feb 1'")
    
    if st.button("✨ Apply Magic Edit"):
        if not edit_instruction:
            st.error("Please type an instruction.")
        else:
            with st.spinner("AI is understanding your instruction..."):
                find_val, replace_val, err = parse_edit_command(edit_instruction)
            
            if err:
                st.error(f"AI Error: {err}")
                st.info("Try using the 'Manual Edit' tab instead.")
            elif find_val is None:
                st.warning("Could not understand what text to find. Please try rephrasing.")
            else:
                st.success(f"AI Plan: Find **'{find_val}'** -> Replace with **'{replace_val}'**")
                
                # Apply Edit
                output_doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                count = 0
                
                for page in output_doc:
                    text_instances = page.search_for(find_val)
                    for rect in text_instances:
                        count += 1
                        # 1. Redact (White out)
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        page.apply_redactions()
                        
                        # 2. Insert new text
                        fontsize = rect.height * 0.8 
                        page.insert_text(
                            point=rect.tl + (0, rect.height * 0.75),
                            text=replace_val,
                            fontsize=fontsize,
                            color=(0, 0, 0)
                        )
                
                if count > 0:
                    st.success(f"✅ Successfully updated {count} places!")
                    
                    output_buffer = io.BytesIO()
                    output_doc.save(output_buffer)
                    output_doc.close()
                    
                    st.download_button(
                        label="Download Edited PDF",
                        data=output_buffer.getvalue(),
                        file_name="magic_edited_document.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning(f"Could not find the text '{find_val}' in the document. Please check the spelling or try Manual Edit.")

# ==========================================
# TAB 2: MANUAL REPLACER
# ==========================================
with tab_manual:
    st.header("Find & Replace Text")
    st.markdown("Manually specify exact text to find and replace.")
    
    col1, col2 = st.columns(2)
    with col1:
        search_text = st.text_input("Find Text (Exact Match)")
    with col2:
        replace_text = st.text_input("Replace With")
    
    match_case = st.checkbox("Match Case", value=True)
    
    if st.button("Preview Replacements"):
        if not search_text:
            st.error("Please enter text to find.")
        else:
            found_count = 0
            for page in doc:
                text_instances = page.search_for(search_text)
                found_count += len(text_instances)
            
            if found_count > 0:
                st.success(f"Found {found_count} instances of '{search_text}'.")
            else:
                st.warning(f"No instances of '{search_text}' found.")

    if st.button("Apply Replacement & Download"):
        if not search_text:
            st.error("Please enter text to find.")
        else:
            # Create a copy of the doc for editing
            output_doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            
            count = 0
            for page in output_doc:
                # Search for text
                text_instances = page.search_for(search_text)
                
                for rect in text_instances:
                    count += 1
                    # 1. Redact (Remove) old text
                    page.add_redact_annot(rect, fill=(1, 1, 1)) # Fill with white
                    page.apply_redactions()
                    
                    # 2. Insert new text
                    # Heuristic to guess font size based on rect height
                    fontsize = rect.height * 0.8 
                    page.insert_text(
                        point=rect.tl + (0, rect.height * 0.75), # Baseline adjustment
                        text=replace_text,
                        fontsize=fontsize,
                        color=(0, 0, 0) # Black text
                    )
            
            if count > 0:
                st.success(f"Replaced {count} instances!")
                
                # Save to buffer
                output_buffer = io.BytesIO()
                output_doc.save(output_buffer)
                output_doc.close()
                
                st.download_button(
                    label="Download Modified PDF",
                    data=output_buffer.getvalue(),
                    file_name="modified_document.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No text found to replace.")

# ==========================================
# TAB 3: STATEMENT ANALYZER (Structure Extraction)
# ==========================================
with tab_extract:
    st.header("Statement Data Extractor")
    st.markdown("Extract structured data like **Dates**, **Amounts**, and **Descriptions** from statements.")
    
    # Extract text from first page for analysis
    page1_text = doc[0].get_text()
    
    st.subheader("Raw Text Preview (Page 1)")
    st.text_area("Content", page1_text, height=200)
    
    st.subheader("Detected Values")
    
    # Simple Regex-based extraction (Simulation of "Deriving Values")
    # 1. Dates
    dates = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', page1_text)
    # 2. Currency
    amounts = re.findall(r'\$?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?', page1_text)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("📅 **Potential Dates**")
        if dates:
            st.dataframe({"Date": list(set(dates))}, use_container_width=True)
        else:
            st.write("No dates found.")
            
    with c2:
        st.write("💰 **Potential Amounts**")
        # Filter out empty or non-money strings
        valid_amounts = [a for a in amounts if any(char.isdigit() for char in a) and len(a) > 1]
        if valid_amounts:
            st.dataframe({"Amount": list(set(valid_amounts))}, use_container_width=True)
        else:
            st.write("No amounts found.")

# ==========================================
# TAB 4: AI ASSISTANT
# ==========================================
with tab_ai:
    st.header("🤖 AI Assistant")
    st.markdown("Ask AI to analyze the document or suggest changes.")
    
    user_prompt = st.text_area("Ask AI about this document:", "Summarize this bank statement and tell me the total balance.")
    
    if st.button("Analyze with AI"):
        if not openai.api_key:
            st.error("OpenAI API Key is required for this feature.")
        else:
            with st.spinner("AI is thinking..."):
                try:
                    # Limit text to avoid token limits (first 2000 chars)
                    context_text = page1_text[:3000]
                    
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful financial assistant. Analyze the following document text."},
                            {"role": "user", "content": f"Document Content:\n{context_text}\n\nQuestion: {user_prompt}"}
                        ]
                    )
                    
                    ai_reply = response.choices[0].message.content
                    st.markdown("### AI Response")
                    st.write(ai_reply)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
