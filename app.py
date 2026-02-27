import streamlit as st
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import io
import re
import os
import openai
from dotenv import load_dotenv
import speech_recognition as sr
import threading

# Load environment variables (for OpenAI key if present)
load_dotenv()
if os.getenv("OPENAI_API_KEY"):
    openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI PDF Master", page_icon="🤖", layout="wide")

st.title("🤖 AI PDF Master: Voice-Controlled PDF Editor")
st.markdown("Use your **voice** to edit PDFs. Say things like *'Replace 2023 with 2024'*.")

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
tab_voice, tab_replace, tab_extract, tab_ai = st.tabs(["🎙️ Voice Edit", "✏️ Manual Edit", "📊 Analyzer", "🤖 AI Chat"])

# Helper function to process voice command with LLM
def parse_voice_command(command_text):
    """
    Uses OpenAI to extract 'find_text' and 'replace_text' from natural language.
    """
    if not openai.api_key:
        return None, None, "OpenAI API Key required for smart parsing."
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a command parser. Extract the 'find' text and 'replace' text from the user's voice command. Return ONLY a JSON object: {\"find\": \"...\", \"replace\": \"...\"}. If the user says 'delete X', replace should be empty string."},
                {"role": "user", "content": command_text}
            ]
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get("find"), result.get("replace"), None
    except Exception as e:
        return None, None, str(e)

# ==========================================
# TAB 1: VOICE EDITOR
# ==========================================
with tab_voice:
    st.header("🎙️ Voice Command Center")
    st.write("Click the button and speak your edit command.")
    st.info("Example: *'Change the date January 1st to February 1st'* or *'Replace Total Balance with Amount Due'*")

    # Session state for voice result
    if "voice_text" not in st.session_state:
        st.session_state.voice_text = ""
    
    if st.button("🎤 Start Listening"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            with st.spinner("Listening... Speak now!"):
                try:
                    audio = r.listen(source, timeout=5)
                    st.session_state.voice_text = r.recognize_google(audio)
                    st.success(f"Heard: \"{st.session_state.voice_text}\"")
                except sr.UnknownValueError:
                    st.error("Could not understand audio.")
                except sr.RequestError as e:
                    st.error(f"Could not request results; {e}")
                except Exception as e:
                    st.error(f"Microphone error: {e}. (Note: Microphone access may not work on deployed web apps due to browser security. Works best locally.)")

    if st.session_state.voice_text:
        st.write("---")
        st.write(f"**Processing Command:** *{st.session_state.voice_text}*")
        
        find_val, replace_val, err = parse_voice_command(st.session_state.voice_text)
        
        if err:
            st.error(f"AI Parsing Error: {err}")
            st.warning("Fallback: Please enter values manually in the 'Manual Edit' tab.")
        elif find_val is not None:
            st.success(f"AI Detected -> Find: **'{find_val}'**, Replace with: **'{replace_val}'**")
            
            if st.button("Confirm & Apply Edit"):
                 # Create a copy of the doc for editing
                output_doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                
                count = 0
                for page in output_doc:
                    # Search for text
                    text_instances = page.search_for(find_val)
                    
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
                            text=replace_val,
                            fontsize=fontsize,
                            color=(0, 0, 0) # Black text
                        )
                
                if count > 0:
                    st.success(f"Successfully replaced {count} occurrences!")
                    
                    # Save to buffer
                    output_buffer = io.BytesIO()
                    output_doc.save(output_buffer)
                    output_doc.close()
                    
                    st.download_button(
                        label="Download Voice-Edited PDF",
                        data=output_buffer.getvalue(),
                        file_name="voice_edited_document.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning(f"Could not find exact text '{find_val}' in the document.")

# ==========================================
# TAB 2: MANUAL REPLACER
# ==========================================
with tab_replace:
    st.header("Find & Replace Text")
    st.markdown("Replace specific text in the PDF. Useful for updating dates, names, or values.")
    
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
