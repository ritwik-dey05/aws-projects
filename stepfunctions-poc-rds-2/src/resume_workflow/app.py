import json, boto3
from common.db_helper import get_db_connection

sfn = boto3.client("stepfunctions")

def lambda_handler(event, context):
    task_id = (event.get("pathParameters") or {}).get("taskId")
    if not task_id:
        qs = event.get("queryStringParameters") or {}
        task_id = qs.get("taskId")
    body = event.get("body") or "{}"
    if isinstance(body, str):
        try: body = json.loads(body)
        except json.JSONDecodeError: body = {}
    qs = event.get("queryStringParameters") or {}
    decision = (body.get("decision") or qs.get("decision") or "").upper()
    comments = body.get("comments") or ""

    if not task_id:
        return {"statusCode":400,"body":json.dumps({"error":"taskId is required"})}
    if decision not in {"APPROVE","REJECT"}:
        return {"statusCode":400,"body":json.dumps({"error":"decision must be APPROVE or REJECT"})}

# Fetch task token from DB
    conn = get_db_connection()
    token = None
    with conn, conn.cursor() as cur:
        cur.execute("SELECT task_token FROM approval_tasks WHERE task_id=%s",(task_id,))
        row = cur.fetchone()
        if row: token = row[0]
    conn.close()

    if not token:
        return {"statusCode":404,"body":json.dumps({"error":"No task token found (already actioned or invalid)."})}

    payload = {"taskId":task_id,"decision":decision,"comments":comments}
    if decision=="APPROVE":
        sfn.send_task_success(taskToken=token, output=json.dumps(payload))
    else:
        sfn.send_task_failure(taskToken=token, error="Rejected", cause=json.dumps(payload))
    return {"statusCode":200,"body":json.dumps({"status":"ok","taskId":task_id,"decision":decision})}
