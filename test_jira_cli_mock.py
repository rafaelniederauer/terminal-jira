import unittest
from unittest.mock import MagicMock, patch
import os
from jira_cli import ConfigLoader, JiraClient, IssueParser

class TestJiraCLI(unittest.TestCase):
    def setUp(self):
        # Mock environment variables
        os.environ["JIRA_URL"] = "https://mock.jira.com"
        os.environ["JIRA_USERNAME"] = "user"
        os.environ["JIRA_PASSWORD"] = "pass"
        os.environ["FIELD_STORY_POINTS"] = "customfield_10006"
        os.environ["FIELD_SPRINTS"] = "customfield_10004"
        
        self.config = ConfigLoader()

    def test_config_loader(self):
        self.assertEqual(self.config.jira_url, "https://mock.jira.com")
        self.assertEqual(self.config.field_story_points, "customfield_10006")

    def test_issue_parser(self):
        parser = IssueParser(self.config)
        
        mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Dev"},
                    "priority": {"name": "High"},
                    "issuetype": {"name": "Story"},
                    "customfield_10006": 5.0,
                    "customfield_10004": [
                        "com.atlassian.greenhopper.service.sprint.Sprint@123[id=1,rapidViewId=1,state=ACTIVE,name=Sprint 1,startDate=...,endDate=...,completeDate=...,sequence=1]"
                    ],
                    "customfield_10000": "EPIC-1"
                }
            }
        ]
        
        parsed = parser.parse(mock_issues)
        
        self.assertEqual(len(parsed), 1)
        item = parsed[0]
        self.assertEqual(item["Key"], "TEST-1")
        self.assertEqual(item["Sprint"], "Sprint 1")
        self.assertEqual(item["Points"], "5.0")
        self.assertEqual(item["Epic Link"], "EPIC-1")

    @patch('requests.get')
    def test_client_search(self, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                 {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Dev"},
                    "priority": {"name": "High"},
                    "issuetype": {"name": "Story"},
                    "customfield_10006": 5.0,
                    "customfield_10004": ["name=Sprint 1"],
                    "customfield_10000": "EPIC-1"
                }
            }
            ],
            "total": 1
        }
        mock_get.return_value = mock_response

        client = JiraClient(self.config)
        issues = client.search_issues("project = TEST")
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["key"], "TEST-1")

if __name__ == '__main__':
    unittest.main()
