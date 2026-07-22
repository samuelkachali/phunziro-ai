import os
import streamlit as st
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv
from paychangu_helper import create_checkout_session, verify_payment

load_dotenv()

# Setup Gemini API Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Streamlit Page Config
st.set_page_config(page_title="PhunziroAI 🎓 - Exam Prep", page_icon="🎓", layout="centered")

# Initialize Session States
if "paid_user" not in st.session_state:
    st.session_state.paid_user = False
if "current_tx_ref" not in st.session_state:
    st.session_state.current_tx_ref = None

query_params = st.query_params

if "tx_ref" in query_params:
    ref = query_params["tx_ref"]
    
    # Run verification check against PayChangu API
    with st.spinner("Verifying your payment status..."):
        if verify_payment(ref):
            st.session_state.paid_user = True
            st.success("🎉 Payment verified successfully! Full access unlocked.")
        else:
            st.error("⚠️ Payment verification failed or transaction was canceled.")

st.title("🎓 PhunziroAI")
st.subheader("Transform your lecture slides into practice exam quizzes in seconds!")

# Handle URL parameters for PayChangu Callbacks
query_params = st.query_params
if "tx_ref" in query_params:
    ref = query_params["tx_ref"]
    if verify_payment(ref):
        st.session_state.paid_user = True
        st.success("🎉 Payment verified successfully! Access granted.")

# Free vs Paid Status Banner
if st.session_state.paid_user:
    st.info("🔓 Unlimited Pass Active")
else:
    st.warning("🔒 Free Mode: 1 Free Test Quiz per session. Unlock full access for MWK 500.")

st.markdown("---")

# File Upload Section
uploaded_file = st.file_uploader("Upload Lecture Slides (PDF)", type=["pdf"])

def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        full_text = extract_pdf_text(uploaded_file)
    
    st.success(f"Successfully processed {len(uploaded_file.name)}. ({len(full_text.split())} words loaded)")
    
    action = st.radio("Choose AI Action:", ["Generate Practice Quiz (10 MCQs)", "Summary & Key Concepts"])
    
    if st.button("Generate Output"):
        # Check payment gate if user hasn't paid
        if not st.session_state.paid_user:
            st.error("Access Restricted! Please unlock daily access via Airtel Money / Mpamba below.")
        else:
            with st.spinner("Gemini is analyzing your material..."):
                if action == "Generate Practice Quiz (10 MCQs)":
                    prompt = f"""
                    You are a university professor preparing a final exam.
                    Based strictly on the text provided below, generate 10 multiple-choice questions (MCQs) with 4 options each (A, B, C, D).
                    Provide the correct answer and a brief explanation for each question.
                    
                    Lecture Content:
                    {full_text[:12000]}
                    """
                else:
                    prompt = f"""
                    Summarize the key study points from these lecture notes into bullet points for quick exam revision.
                    
                    Lecture Content:
                    {full_text[:12000]}
                    """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=prompt
                )
                
                st.markdown("### AI Output")
                st.write(response.text)

st.markdown("---")

# Payment Modal / Section
if not st.session_state.paid_user:
    st.subheader("💳 Unlock Daily Unlimited Pass (MWK 500)")
    st.write("Pay seamlessly via Airtel Money or TNM Mpamba using PayChangu.")
    
    email_input = st.text_input("Enter your Email (for payment receipt):", value="student@unima.mw")
    
    if st.button("Pay MWK 500 via Mobile Money"):
        res = create_checkout_session(amount=500, user_email=email_input)
        if res["status"]:
            st.session_state.current_tx_ref = res["tx_ref"]
            st.markdown(f"[👉 Click Here to Complete Payment on PayChangu]({res['checkout_url']})")
        else:
            st.error(f"Error: {res['message']}")