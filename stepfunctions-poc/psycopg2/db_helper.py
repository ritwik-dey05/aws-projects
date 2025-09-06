import boto3
import json
import os
import psycopg2

# Cached database connection
db_connection = None

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    Caches the connection for subsequent invocations.
    """
    global db_connection
    if db_connection:
        return db_connection

    secret_name = os.environ['DB_SECRET_ARN']
    region_name = os.environ['AWS_REGION']

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        print(f"Error getting secret: {e}")
        raise e
    else:
        secret = json.loads(get_secret_value_response['SecretString'])
        
        try:
            print("Connecting to the database...")
            db_connection = psycopg2.connect(
                host=secret['host'],
                port=secret['port'],
                user=secret['username'],
                password=secret['password'],
                dbname=secret['dbname'],
                connect_timeout=5
            )
            return db_connection
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise e