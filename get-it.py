import streamlit as st
import re
import csv
from email import message_from_string
from PyPDF2 import PdfReader
from io import StringIO


# Apply the custom style
def set_page_style():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: black;
            color: white;
        }
        textarea, input, select, button {
            background-color: #333;
            color: white; /* Set default text color */
            border: 1px solid white;
        }
        .stButton > button {
            background-color: #444; /* Button background color */
            color: white; /* Ensure text is always visible */
            border: 1px solid white;
            font-size: 16px; /* Optional: Adjust font size for readability */
        }
        .stButton > button:hover {
            background-color: #555; /* Slightly lighter background on hover */
            color: white; /* Keep text color white on hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def strip_html(content):
    return re.sub(r"<.*?>", "", content)


def extract_details(email_text):
    job_description = re.findall(r"(Required|Experience|Must Have|Nice to Have):(.+)", email_text, re.IGNORECASE)
    job_description_text = "\n".join([f"{key}: {value.strip()}" for key, value in job_description])

    contact_match = re.search(r"\n([A-Z][a-z]+ [A-Z][a-z]+)(?:\n|$)", email_text)
    contact_text = contact_match.group(1) if contact_match else "Not Found"

    salary_match = re.search(r"\$\d+(?:,\d{3})*(?:\.\d{2})?", email_text)
    salary_text = salary_match.group(0) if salary_match else "Not Found"

    other_details = re.sub(r"(Required|Experience|Must Have|Nice to Have):.+", "", email_text, flags=re.IGNORECASE)
    other_details = re.sub(r"[^\n]+?\$\d+[^\n]+?\n", "", other_details)
    other_details = re.sub(r"\n([A-Z][a-z]+ [A-Z][a-z]+)(?:\n|$)", "", other_details)
    other_details = other_details.strip()

    return {
        "Job Description": job_description_text or "Not Found",
        "Contact": contact_text,
        "Salary": salary_text,
        "Other Details": other_details,
    }


def parse_eml(file_content):
    email_message = message_from_string(file_content)
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                return strip_html(part.get_payload(decode=True).decode())
            elif part.get_content_type() == "text/html":
                return strip_html(part.get_payload(decode=True).decode())
    else:
        return strip_html(email_message.get_payload(decode=True).decode())


def parse_pdf(file_content):
    pdf_reader = PdfReader(file_content)
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text()
    return pdf_text


def generate_csv(details):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job", "Job Details"])
    for key, value in details.items():
        writer.writerow([key, value])
    return output.getvalue()


# Apply the custom style
set_page_style()

# Streamlit app
st.title("Email Job Details Extractor and Converter")
uploaded_file = st.file_uploader("Upload an email file (.txt, .eml, or .pdf)", type=["txt", "eml", "pdf"])

if uploaded_file:
    if uploaded_file.type == "text/plain":
        email_content = strip_html(uploaded_file.read().decode("utf-8"))
    elif uploaded_file.type == "message/rfc822":
        email_content = parse_eml(uploaded_file.read().decode("utf-8"))
    elif uploaded_file.type == "application/pdf":
        email_content = parse_pdf(uploaded_file)

    st.text_area("Uploaded Email Content", email_content, height=200)
    st.header("Extracted Details")
    details = extract_details(email_content)
    for key, value in details.items():
        st.write(f"**{key}:** {value}")

    csv_data = generate_csv(details)
    st.download_button(
        label="Download as CSV",
        data=csv_data,
        file_name="extracted_details.csv",
        mime="text/csv"
    )
