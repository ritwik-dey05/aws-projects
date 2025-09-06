import json
import os
import psycopg2
from db_helper import get_db_connection

def lambda_handler(event, context):
    """
    Updates the final status of the task in PostgreSQL.
    """
    conn = get_db_connection()
    conn.autocommit = True

    try:
        task_id = event['taskId']
        status = event['status']
        comments = event.get('comments', '')

        with conn.cursor() as cur:
            sql_update = """
                UPDATE approval_tasks 
                SET status = %s, comments = %s, updated_at = NOW()
                WHERE task_id = %s;
            """
            cur.execute(sql_update, (status, comments, task_id))
        
        return {'status': 'success'}
    except (Exception, psycopg2.Error) as e:
        print(f"Error updating task status: {e}")
        raise e
