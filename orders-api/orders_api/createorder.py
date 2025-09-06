import json
import boto3
import os

from botocore.exceptions import ClientError


# import requests


def lambda_handler(event, context):
    msg = ""
    status_code: 500
    try:
        db = boto3.resource("dynamodb")
        order = json.loads(event["body"])
        table_name = os.environ.get('ORDER_TABLE')
        table = db.Table(table_name)
        response = table.put_item(TableName=table_name, Item=order)
        print(response)
        msg = "Order created successfully"
        status_code = 200
    except ClientError as e:
        status_code = 500
        print(e)
    return {
        "statusCode": status_code,
        "body": json.dumps({
            "message": msg,
            # "location": ip.text.replace("\n", "")
        }),
    }
