import os
import json
import psycopg2
import boto3

def _get_secret(secret_arn: str, region: str) -> dict:
    sm = boto3.client("secretsmanager", region_name=region)
    resp = sm.get_secret_value(SecretId=secret_arn)
    if "SecretString" in resp:
        return json.loads(resp["SecretString"])
    return json.loads(resp["SecretBinary"].decode())

def get_db_connection():
    secret_arn = os.environ["DB_SECRET_ARN"]
    region = os.environ["AWS_REGION"]
    secret = _get_secret(secret_arn, region)

    host = os.environ["DB_HOST"]
    port = int(os.environ.get("DB_PORT", "5432"))
    dbname = os.environ["DB_NAME"]
    user = secret.get("username") or secret.get("user")
    password = secret["password"]

    return psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, connect_timeout=5)
