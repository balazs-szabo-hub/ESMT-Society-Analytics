import re
import time
import streamlit as st
import os
import glob
from dotenv import load_dotenv
from docx import Document
from huggingface_hub import InferenceClient
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE

def load_docs(folder="docs"):
    """Load all .docx files from the docs/ folder and return their text."""
    texts = []
    for filepath in sorted(glob.glob(os.path.join(folder, "*.docx"))):
        doc = Document(filepath)
        content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        name = os.path.basename(filepath)
        texts.append(f"--- Document: {name} ---\n{content}")
    return "\n\n".join(texts)

# 1. Page Configuration
st.set_page_config(page_title="Retail Ethics Demo", page_icon="🛍️")

# Sidebar with example use cases
EXAMPLE_CASES = [
    "Audit facial recognition technology used in retail stores",
    "Evaluate dynamic pricing algorithms in e-commerce",
    "Assess automated checkout systems replacing cashiers",
    "Review AI-powered product recommendation engines",
    "Analyze customer surveillance via loyalty programs",
    "Examine AI-generated product descriptions and images",
]

with st.sidebar:
    st.header("💡 Example Use Cases")
    for case in EXAMPLE_CASES:
        if st.button(case, use_container_width=True):
            st.session_state.selected_case = case
            st.rerun()

st.title("🛒 Retail AI Ethics Auditor")
st.markdown("---")

# 2. Secure Token Handling
# In Codespaces, you'll set this in your Secrets.
# For local testing, you can paste it here (but don't push it to GitHub!)
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

# 3. Initialize the AI Client
client = InferenceClient("Qwen/Qwen2.5-7B-Instruct", token=hf_token)

# 4. Load reference documents & Initialize Chat History
docs_context = load_docs()
full_system_prompt = SYSTEM_PROMPT
if docs_context:
    full_system_prompt += (
        "\n\n### REFERENCE DOCUMENTS:\n"
        "Use the following documents as context when answering questions.\n\n"
        + docs_context
    )

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

# 5. Display Chat History
for message in st.session_state.messages:
    if message["role"] != "system": # Don't show the background instructions
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 6. Chat Input Logic
prompt = st.chat_input("Ask about a retail AI case (e.g., facial recognition in stores)")

# Handle sidebar selection
if "selected_case" in st.session_state:
    prompt = st.session_state.selected_case
    del st.session_state.selected_case

if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI Response (no validation/retry logic)
    with st.chat_message("assistant"):
        if not hf_token:
            st.error("HF_TOKEN not found! Please add it to your Codespace Secrets.")
        else:
            try:
                output_placeholder = st.empty()
                messages_to_send = list(st.session_state.messages)
                stream = client.chat_completion(
                    messages=messages_to_send,
                    max_tokens=4000,
                    temperature=0.3,
                    stream=True
                )
                response = ""
                for token in stream:
                    if len(token.choices) > 0 and token.choices[0].delta.content is not None:
                        response += token.choices[0].delta.content
                        output_placeholder.markdown(response + "▌")
                output_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")