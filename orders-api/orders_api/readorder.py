import json
import boto3
import os

from decimal import Decimal


# import requests

def decimal_to_str(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def lambda_handler(event, context):
    msg = ""
    status_code: 500
    try:
        db = boto3.resource("dynamodb")
        order_id = int(event["pathParameters"]["id"])
        table_name = os.environ.get('ORDER_TABLE')
        table = db.Table(table_name)
        response = table.get_item(Key={"id": order_id})
        print(f"Response: {response}")
        item = response["Item"]
        print(f"Item: {item}")
        print(f"Item type: {type(item)}")
        item_id = item["id"]
        msg = item
        status_code = 200
        itemjson = json.dumps(item, default=decimal_to_str)
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": itemjson
        }
    except BaseException as e:
        status_code = 500
        print(e)
        return {
            "statusCode": status_code,
            "body": "Error occurd"
        }
