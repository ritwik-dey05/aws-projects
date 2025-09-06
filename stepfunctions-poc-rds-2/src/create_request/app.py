import json, uuid, datetime as dt
from db_helper import get_db_connection

def _now(): return dt.datetime.utcnow()

def lambda_handler(event, context):
    body = event.get("body") or "{}"
    if isinstance(body, str):
        try: body = json.loads(body)
        except json.JSONDecodeError: body = {}
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    assessor_email = (body.get("assessorEmail") or "").strip()
    if not title or not assessor_email:
        return {"statusCode": 400, "body": json.dumps({"error":"title and assessorEmail are required"})}

    qid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    conn = get_db_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO questions (question_id,title,content,created_at) VALUES (%s,%s,%s,%s)",
                        (qid,title,content,_now()))
            cur.execute("""
                INSERT INTO approval_tasks (task_id,question_id,assessor_email,status,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s)
            """,(tid,qid,assessor_email,"PENDING",_now(),_now()))
    finally:
        conn.close()

    return {"statusCode":200,"body":json.dumps({"taskId":tid,"questionId":qid,"assessorEmail":assessor_email,"title":title})}
