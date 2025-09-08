import datetime as dt
from db_helper import get_db_connection

def _now(): return dt.datetime.utcnow()

def lambda_handler(event, context):
    payload = event if isinstance(event, dict) else {}
    task_id = payload.get("taskId")
    decision = payload.get("decision","UNKNOWN")
    comments = payload.get("comments","")
    if not task_id: return {"status":"noop"}

    status_map = {"APPROVE":"APPROVED","REJECT":"REJECTED","TIMED_OUT":"TIMED_OUT","FAILED":"FAILED"}
    new_status = status_map.get(decision, decision)

    conn = get_db_connection()
    with conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE approval_tasks
            SET status=%s, comments=%s, updated_at=%s, task_token=NULL
            WHERE task_id=%s
        """,(new_status, comments, _now(), task_id))
    conn.close()
    return {"status":"updated","taskId":task_id,"statusSet":new_status}
