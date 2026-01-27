# Terminal Jira CLI

A powerful, aesthetic, and flexible terminal application for interacting with Jira. Built with Python, Rich, and Pandas.

## Features

- **Search**: Flexible JQL searching with formatted table output.
- **Grouping**: Aggregate story points and counts by status, assignee, or epic.
- **Pivot Tables**: Generate matrix reports (e.g., Epics vs Status) directly in your terminal.
- **Management**: Create and edit issues with support for custom fields (Story Points, Epic Links).
- **Sprint Management**: Add or remove issues from sprints by name.
- **Aesthetic**: Rich-formatted output with panels, colors, and progress bars.
- **Anonymization**: Demo-ready mode to redact sensitive summaries.
- **Configurable**: Works with Jira Data Center and Jira Cloud via environment variables.

---

## 1. Setup

### Installation
Clone the repository and install dependencies:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Copy the example environment file and fill in your Jira details:

```bash
cp .env.example .env
```

Edit `.env` with:
- `JIRA_URL`: Your Jira instance URL.
- `JIRA_USERNAME`: Your username (or email for Cloud).
- `JIRA_PASSWORD`: Your password (or API Token for Cloud).
- `FIELD_*`: Custom field IDs for your specific Jira instance.

---

## 2. Usage

Available commands: `search`, `view`, `create`, `edit`.

### Search issues
```bash
# Basic search
python jira_cli.py search --jql "project = PROJ"

# Search with sorting
python jira_cli.py search --jql "project = PROJ" --sort status

# Search with Epic summaries
python jira_cli.py search --jql "project = PROJ" --epic-name
```

### Grouping & Aggregation
```bash
# Group by Status (Count + Total Points)
python jira_cli.py search --jql "project = PROJ" --group-by Status

# Group by Epic and Status
python jira_cli.py search --jql "project = PROJ" --epic-name --group-by "Epic Summary,Status"
```

### Pivot Tables
Generate a matrix of Story Points:
```bash
python jira_cli.py search --jql "project = PROJ" --epic-name --pivot-rows "Epic Summary" --pivot-cols "Status" --pivot-values "Points"
```

### Detailed View
```bash
python jira_cli.py view PROJ-123
```

### Create & Edit
```bash
# Create
python jira_cli.py create --project PROJ --summary "Task Name" --type Task

# Edit
python jira_cli.py edit PROJ-123 --points 5 --status "In Progress"

# Sprint Management
python jira_cli.py edit PROJ-123 --sprint "Sprint 5"
python jira_cli.py edit PROJ-123 --clear-sprint
```

---

## 3. Advanced Configuration

### Jira Cloud Support
If using Jira Cloud, update the API version in your `.env`:
```bash
JIRA_API_SEARCH_ENDPOINT=/rest/api/3/search
JIRA_API_ISSUE_ENDPOINT=/rest/api/3/issue
```

### Demo Mode
Redact ticket summaries and descriptions for public presentations:
```bash
JIRA_ANONYMIZE=True python jira_cli.py search --jql "..."
```
