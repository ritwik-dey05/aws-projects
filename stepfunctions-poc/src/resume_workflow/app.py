import json
import boto3
import os
import psycopg2
from db_helper import get_db_connection

sfn_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Triggered by API Gateway. Resumes the paused Step Function execution.
    """
    conn = get_db_connection()
    conn.autocommit = True

    try:
        body = json.loads(event['body'])
        task_id = body['taskId']
        action = body['action']
        comments = body.get('comments', '')

        if action not in ['approved', 'rejected']:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid action'})}

        # 1. Retrieve the task token from PostgreSQL
        with conn.cursor() as cur:
            sql_select = "SELECT task_token FROM approval_tasks WHERE task_id = %s;"
            cur.execute(sql_select, (task_id,))
            result = cur.fetchone()

            if not result or not result[0]:
                return {'statusCode': 404, 'body': json.dumps({'error': 'Task not found or completed.'})}
            
            task_token = result[0]

            # 2. Resume the Step Function execution
            sfn_client.send_task_success(
                taskToken=task_token,
                output=json.dumps({'action': action, 'comments': comments})
            )

            # 3. Remove the task token from the DB
            sql_clear_token = "UPDATE approval_tasks SET task_token = NULL WHERE task_id = %s;"
            cur.execute(sql_clear_token, (task_id,))

        return {'statusCode': 200, 'body': json.dumps({'message': f'Task {action} successfully.'})}

    except (Exception, psycopg2.Error) as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'An internal error occurred.'})}
