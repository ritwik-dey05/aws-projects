import json, uuid, datetime as dt
from db_helper import get_db_connection

# import requests

def _now(): return dt.datetime.utcnow()

def lambda_handler(event, context):
    payload = event["body"]
    print(f"CreateRequest:: incoming payload: {payload}")
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    try:
        return save_to_db(payload)
    except Exception as e:
        print(e)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }

def save_to_db(body):
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    assessor_email = (body.get("assessorEmail") or "").strip()
    if not title or not assessor_email:
        return {"statusCode": 400, "body": json.dumps({"error": "title and assessorEmail are required"})}

    qid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    conn = get_db_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO questions (question_id,title,content,created_at) VALUES (%s,%s,%s,%s)",
                        (qid, title, content, _now()))
            cur.execute("""
                    INSERT INTO approval_tasks (task_id,question_id,assessor_email,status,created_at,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (tid, qid, assessor_email, "PENDING", _now(), _now()))
    finally:
        conn.close()

    return {"statusCode": 200,
            "body": json.dumps({"taskId": tid, "questionId": qid, "assessorEmail": assessor_email, "title": title})}

