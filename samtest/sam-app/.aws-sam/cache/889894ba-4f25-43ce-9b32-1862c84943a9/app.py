import json, boto3, os
from db_helper import get_db_connection

# Ensure we're using the same region as the state machine
region = os.environ.get("AWS_REGION", "us-east-1")
sfn = boto3.client("stepfunctions", region_name=region)

def lambda_handler(event, context):
    print(f"Function invoked with event: {json.dumps(event)}")

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

    print(f"Processing task {task_id} with decision {decision}")

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

    print(f"Token length: {len(token)}")
    print(f"Token starts with: {token[:50]}...")
    print(f"Token ends with: ...{token[-50:]}")
    print(f"Full token (first 200 chars): {token[:200]}")
    
    # Validate token format
    if not token or len(token) < 100:  # Task tokens are typically much longer
        print(f"WARNING: Token seems too short: {len(token)} characters")
        return {"statusCode":400,"body":json.dumps({"error":"Invalid task token format"})}
    
    # Check if token contains expected base64 characters
    import base64
    try:
        # Task tokens should be valid base64
        base64.b64decode(token, validate=True)
        print("Token appears to be valid base64")
    except Exception as e:
        print(f"Token validation failed: {e}")
        return {"statusCode":400,"body":json.dumps({"error":"Invalid task token encoding"})}
    
    payload = {"taskId":task_id,"decision":decision,"comments":comments}
    print(f"Sending task result to Step Functions: {json.dumps(payload)}")
    try:
        if decision=="APPROVE":
            print("Calling send_task_success...")
            response = sfn.send_task_success(taskToken=token, output=json.dumps(payload))
            print(f"send_task_success response: {response}")
        else:
            print("Calling send_task_failure...")
            response = sfn.send_task_failure(taskToken=token, error="Rejected", cause=json.dumps(payload))
            print(f"send_task_failure response: {response}")
        print("Step Functions call completed successfully")
        
        # Clean up the task from database
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM approval_tasks WHERE task_id=%s", (task_id,))
        conn.close()
        print(f"Task {task_id} removed from database")
        
    except Exception as e:
        print(f"Error calling Step Functions: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"AWS Error Response: {e.response}")
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            print(f"AWS Error Code: {error_code}")
            print(f"AWS Error Message: {error_msg}")
            
            # Common Step Functions errors
            if error_code == 'TaskDoesNotExist':
                print("ERROR: Task token is invalid or already used")
            elif error_code == 'TaskTimedOut':
                print("ERROR: Task has timed out")
            elif error_code == 'InvalidToken':
                print("ERROR: Task token format is invalid")
                
        return {"statusCode":500,"body":json.dumps({"error":f"Step Functions error: {str(e)}"})}
