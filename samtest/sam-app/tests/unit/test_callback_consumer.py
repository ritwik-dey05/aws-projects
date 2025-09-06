import json
import unittest.mock as mock
import sys
import os

# Add the callback_consumer directory to path
callback_consumer_path = os.path.join(os.path.dirname(__file__), '..', '..', 'callback_consumer')
sys.path.insert(0, callback_consumer_path)

def test_callback_consumer():
    # Mock the db_helper module before importing app
    with mock.patch.dict('sys.modules', {'db_helper': mock.MagicMock()}):
        # Mock the get_db_connection function
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        sys.modules['db_helper'].get_db_connection.return_value = mock_conn
        
        # Now import and test the app
        from app import lambda_handler
        
        # Test event
        event = {
            "Records": [{
                "messageId": "test-message-id-1",
                "body": json.dumps({
                    "taskId": "task-123",
                    "assessorEmail": "test@example.com", 
                    "title": "Test Task",
                    "taskToken": "token-123"
                })
            }]
        }
        
        # Call the function
        result = lambda_handler(event, {})
        
        # Verify mocks were called
        sys.modules['db_helper'].get_db_connection.assert_called_once()
        mock_cursor.execute.assert_called_once()
        
        print("✅ Test passed - DB operations were mocked successfully")
        print(f"Result: {result}")
        print(f"DB execute called with: {mock_cursor.execute.call_args}")

if __name__ == "__main__":
    test_callback_consumer()