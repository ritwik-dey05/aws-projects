import os
import ssl
import smtplib
from email.message import EmailMessage
import boto3

def send_email(subject: str, body: str, to_address: str):
    print(f"Sending email to {to_address} with subject '{subject}'")
    topic_arn = os.getenv("SNS_TOPIC_ARN")
    if topic_arn:
        sns = boto3.client("sns")
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],
            Message=f"To: {to_address}\n\n{body}",
            MessageAttributes={"recipient": {"DataType": "String", "StringValue": to_address}}
        )
        return {"status": "sent_via_sns"}

'''
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SENDER_EMAIL")
    region = os.getenv("AWS_REGION", "us-east-1")
    endpoint = os.getenv("SMTP_ENDPOINT", f"email-smtp.{region}.amazonaws.com")
    port = int(os.getenv("SMTP_PORT", "465"))

    if not all([smtp_user, smtp_pass, sender]):
        return {"status": "not_configured"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(endpoint, port, context=ctx) as s:
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
    return {"status": "sent_via_ses_smtp"}
'''
