import json
import boto3
import os
import psycopg2
from db_helper import get_db_connection

ses_client = boto3.client('ses')
SENDER_EMAIL = os.environ['SENDER_EMAIL']

def lambda_handler(event, context):
    """
    Triggered by SQS. Stores the task token in PostgreSQL and sends an email.
    """
    conn = get_db_connection()
    conn.autocommit = True

    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            task_token = message_body['taskToken']
            task_details = message_body['input']

            task_id = task_details['taskResult']['taskId']
            assessor_email = task_details['taskResult']['assignedTo']

            # 1. Store the taskToken in the approval_tasks table
            with conn.cursor() as cur:
                sql_update = "UPDATE approval_tasks SET task_token = %s WHERE task_id = %s;"
                cur.execute(sql_update, (task_token, task_id))

            # 2. Send an email notification to the assessor
            subject = "Approval Task Assigned"
            body_text = f"A new task has been assigned for your approval. Task ID: {task_id}"
            ses_client.send_email(
                Source=SENDER_EMAIL,
                Destination={'ToAddresses': [assessor_email]},
                Message={'Subject': {'Data': subject}, 'Body': {'Text': {'Data': body_text}}}
            )
            print(f"Successfully processed task {task_id}")

        except (Exception, psycopg2.Error) as e:
            print(f"Error processing SQS message: {e}")
            raise e
