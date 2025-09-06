import os, json, uuid, boto3, datetime as dt

sfn = boto3.client("stepfunctions")
SM_ARN = os.environ["STATE_MACHINE_ARN"]

def _json(event):
    body = event.get("body") or "{}"
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    return body

def handler(event, _ctx):
    payload = _json(event)
    name = f"approval-{uuid.uuid4()}"
    resp = sfn.start_execution(
        stateMachineArn=SM_ARN,
        name=name,
        input=json.dumps(payload)
    )
    # 202 Accepted: execution started
    return {
        "statusCode": 202,
        "body": json.dumps({
            "executionArn": resp["executionArn"],
            "startDate": resp["startDate"].isoformat()
        })
    }