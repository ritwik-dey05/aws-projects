import json
import os
import psycopg2
# Assuming db_helper.py contains the get_db_connection function
from db_helper import get_db_connection

def lambda_handler(event, context):
    """
    Starts the workflow, creates a question record, and an approval task record in PostgreSQL.
    """
    conn = get_db_connection()
    conn.autocommit = True  # Autocommit for simplicity, or manage transactions explicitly

    try:
        with conn.cursor() as cur:
            # Extract data from the initial payload
            question_text = event['question']
            options = event['options']
            correct_answer = event['correctAnswer']
            assigned_by = event['assignedBy']
            assigned_to = event['assignedTo']

            # 1. Save the question to the questions table
            sql_insert_question = """
                INSERT INTO questions (question_text, options, correct_answer)
                VALUES (%s, %s, %s) RETURNING question_id;
            """
            cur.execute(sql_insert_question, (question_text, json.dumps(options), correct_answer))
            question_id = cur.fetchone()[0]

            # 2. Create a record in the approval_tasks table
            sql_insert_task = """
                INSERT INTO approval_tasks (question_id, assigned_by, assigned_to, status)
                VALUES (%s, %s, %s, %s) RETURNING task_id;
            """
            cur.execute(sql_insert_task, (question_id, assigned_by, assigned_to, 'PENDING'))
            task_id = cur.fetchone()[0]

            # Return the taskId and questionId for the next steps
            return {
                'statusCode': 200,
                'body': json.dumps('Request created successfully!'),
                'taskId': str(task_id),
                'questionId': str(question_id),
                'assignedTo': assigned_to
            }

    except (Exception, psycopg2.Error) as e:
        print(f"Database error: {e}")
        # Consider rolling back if not using autocommit
        raise e
