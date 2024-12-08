import imaplib
import email
from email.header import decode_header
import google.generativeai as genai
import typing_extensions as typing
from datetime import datetime, timedelta
import json

# Define the schema for the email classification
class EmailClassification(typing.TypedDict):
    subject: str
    is_purchase_order: bool
    matched_keywords: list[str]

# Configure the Gemini model
genai.configure(api_key="AIzaSyCYYReYEVXG1yxdAV7HAnmZ_1LQ8OK7AGw")
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Email account credentials
username = "sarthak.bhardwaj21b@iiitg.ac.in"
password = "jshi mktk vixd nbbx"
imap_server = "imap.gmail.com"

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(imap_server)
mail.login(username, password)

# Select the mailbox you want to use
mail.select("inbox")

# Calculate the date for filtering (yesterday's date in "dd-MMM-yyyy" format)
yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")

# Search for emails received since yesterday
status, email_ids = mail.search(None, f'SINCE {yesterday}')

# Fetch the email subjects and bodies
emails = []
for e_id in email_ids[0].split():
    status, email_data = mail.fetch(e_id, "(RFC822)")
    for response_part in email_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()
            emails.append({"subject": subject, "body": body})

# Close the mailbox and logout
mail.close()
mail.logout()

# Prepare the prompt for the model
prompts = []
for email in emails:
    prompts.append(f"Classify whether the following email subject is a purchase order: {email['subject']}")
    prompts.append(f"If not, classify based on the email body: {email['body']}")

# Generate content
result = model.generate_content(
    "\n".join(prompts),
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=list[EmailClassification]
    ),
)

# Extract the classified emails from the result
classified_emails = json.loads(result.candidates[0].content.parts[0].text)

# Initialize lists for accepted and rejected emails
accepted_po_emails = []
rejected_emails = []

# Create a mapping between the original emails and their classification results
email_classification_map = {email['subject']: classification for email, classification in zip(emails, classified_emails)}

# Process the results
for email in emails:
    classification = email_classification_map[email['subject']]
    if classification['is_purchase_order']:
        accepted_po_emails.append(email)
    else:
        rejected_emails.append(email)

# # Print accepted purchase order emails
# print("Accepted Purchase Order Emails:")
# for po_email in accepted_po_emails:
#     print(f"Subject: {po_email['subject']}")
#     print(f"Body: {po_email['body']}")
#     print("---")

# # Print rejected emails
# print("Rejected Emails:")
# for rejected_email in rejected_emails:
#     print(f"Subject: {rejected_email['subject']}")
#     print(f"Body: {rejected_email['body']}")
#     print("---")

