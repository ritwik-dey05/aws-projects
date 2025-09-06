import json, os, datetime as dt
from db_helper import get_db_connection

APP_BASE_URL = os.getenv("APP_BASE_URL", "https://example.com")
def _now(): return dt.datetime.utcnow()

def lambda_handler(event, context):
    failures = []
    for rec in event.get("Records", []):
        try:
            body = rec["body"]
            print(f"Callback_Consumer:: Received message: {body}")
            try: payload = json.loads(body)
            except json.JSONDecodeError: payload = json.loads(json.loads(body))

            task_id = payload["taskId"]
            assessor_email = payload["assessorEmail"]
            title = payload.get("title","")
            token = payload["taskToken"]

            conn = get_db_connection()
            with conn, conn.cursor() as cur:
                cur.execute("UPDATE approval_tasks SET task_token=%s, updated_at=%s WHERE task_id=%s",
                            (token,_now(),task_id))
            conn.close()

            approve = f"{APP_BASE_URL}/requests/{task_id}/decision?decision=APPROVE"
            reject  = f"{APP_BASE_URL}/requests/{task_id}/decision?decision=REJECT"
            subject = f"Approval required: {title}"
            bodytxt = f"You have a pending approval task.\n\nTask ID: {task_id}\nTitle: {title}\n\nApprove: {approve}\nReject: {reject}\n"
            print(f"Callback_Consumer:: Sending Email: {bodytxt}")
            #send_email(subject, bodytxt, assessor_email)
        except Exception as e:
            failures.append({"itemIdentifier": rec.get("messageId","unknown")})
    if failures: return {"batchItemFailures": failures}
    return {"status":"ok"}
