import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add current dir to path to find jira_cli
sys.path.append(os.getcwd())

from jira_cli import ConfigLoader, JiraClient

class TestJiraCLIV2(unittest.TestCase):
    def setUp(self):
        os.environ["JIRA_URL"] = "https://mock.jira.com"
        os.environ["JIRA_USERNAME"] = "user"
        os.environ["JIRA_PASSWORD"] = "pass"
        os.environ["JIRA_API_ISSUE_ENDPOINT"] = "/rest/api/2/issue"
        
        self.config = ConfigLoader()
        self.client = JiraClient(self.config)

    @patch('requests.post')
    def test_create_issue(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"key": "TEST-100", "self": "http://link"}
        mock_post.return_value = mock_response

        fields = {
            "project": {"key": "PROJ"},
            "summary": "New Issue",
            "issuetype": {"name": "Task"}
        }
        
        result = self.client.create_issue(fields)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "TEST-100")
        
        # Verify call args
        args, kwargs = mock_post.call_args
        self.assertIn("/rest/api/2/issue", args[0])
        self.assertEqual(kwargs["json"]["fields"]["summary"], "New Issue")

    @patch('requests.put')
    def test_edit_issue(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        fields = {"summary": "Updated Summary"}
        success = self.client.edit_issue("TEST-100", fields)
        
        self.assertTrue(success)
        
        # Verify call args
        args, kwargs = mock_put.call_args
        self.assertIn("/rest/api/2/issue/TEST-100", args[0])
        self.assertEqual(kwargs["json"]["fields"]["summary"], "Updated Summary")

    @patch('requests.put')
    @patch('requests.get')
    def test_edit_sprint(self, mock_get, mock_put):
        # Mock Search for Sprint Resolution
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        # Mock issue with sprint field
        mock_search_response.json.return_value = {
            "issues": [{
                "fields": {
                    "customfield_10004": [
                        "com.atlassian.greenhopper.service.sprint.Sprint@123[id=999,name=Sprint X,state=ACTIVE]"
                    ]
                }
            }]
        }
        mock_get.return_value = mock_search_response
        
        # Mock Edit
        mock_put_response = MagicMock()
        mock_put_response.status_code = 204
        mock_put.return_value = mock_put_response
        
        # Test get_sprint_id directly first
        sprint_id = self.client.get_sprint_id("Sprint X")
        self.assertEqual(sprint_id, 999)

if __name__ == '__main__':
    unittest.main()
