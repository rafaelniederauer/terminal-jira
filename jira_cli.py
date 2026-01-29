import os
import sys
import argparse
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from datetime import datetime

# Initialize Rich Console
console = Console()

class ConfigLoader:
    """
    Loads configuration from environment variables.
    """
    def __init__(self):
        load_dotenv()
        self.jira_url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME")
        self.password = os.getenv("JIRA_PASSWORD")
        
        # API Endpoints
        self.endpoint_search = os.getenv("JIRA_API_SEARCH_ENDPOINT", "/rest/api/2/search")
        self.endpoint_issue = os.getenv("JIRA_API_ISSUE_ENDPOINT", "/rest/api/2/issue")
        
        # Custom Fields Mapping
        self.field_story_points = os.getenv("FIELD_STORY_POINTS", "customfield_10006")
        self.field_sprints = os.getenv("FIELD_SPRINTS", "customfield_10004")
        self.field_epic_link = os.getenv("FIELD_EPIC_LINK", "customfield_10000")
        self.field_activity_type = os.getenv("FIELD_ACTIVITY_TYPE", "customfield_12203")
        self.field_root_request = os.getenv("FIELD_ROOT_REQUEST", "customfield_11306")
        self.field_activity_type = os.getenv("FIELD_ACTIVITY_TYPE", "customfield_12203")
        self.field_root_request = os.getenv("FIELD_ROOT_REQUEST", "customfield_11306")
        self.field_parent_link = os.getenv("FIELD_PARENT_LINK", "customfield_11301")
        
        # Anonymization
        self.anonymize = os.getenv("JIRA_ANONYMIZE", "False").lower() == "true"

    def validate(self):
        if not self.jira_url or not self.username or not self.password:
            console.print("[red]Error: Missing configuration. Please check your .env file.[/red]")
            console.print("Ensure JIRA_URL, JIRA_USERNAME, and JIRA_PASSWORD are set.")
            sys.exit(1)

class JiraClient:
    """
    Handles interactions with the Jira API.
    """
    def __init__(self, config):
        self.config = config
        self.auth = HTTPBasicAuth(self.config.username, self.config.password)
        self.auth = HTTPBasicAuth(self.config.username, self.config.password)
        self.headers = {"Accept": "application/json"}
        self.epic_cache = {}

    def get_epic_summary(self, epic_link):
        if not epic_link:
            return ""
        if epic_link in self.epic_cache:
            return self.epic_cache[epic_link]
            
        url = f"{self.config.jira_url}{self.config.endpoint_issue}/{epic_link}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code == 200:
                summary = response.json().get("fields", {}).get("summary", "Unknown")
                self.epic_cache[epic_link] = summary
                return summary
        except Exception:
            pass
        return "Error"

    def create_issue(self, fields):
        url = f"{self.config.jira_url}{self.config.endpoint_issue}"
        try:
            response = requests.post(url, json={"fields": fields}, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code in (201, 200):
                return response.json()
            else:
                console.print(f"[red]Error creating issue: {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Connection Error: {e}[/red]")
            return None

    def edit_issue(self, key, fields):
        url = f"{self.config.jira_url}{self.config.endpoint_issue}/{key}"
        try:
            response = requests.put(url, json={"fields": fields}, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code in (204, 200):
                return True
            else:
                console.print(f"[red]Error editing issue: {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Connection Error: {e}[/red]")
            return False

    def create_issue(self, fields):
        url = f"{self.config.jira_url}{self.config.endpoint_issue}"
        try:
            response = requests.post(url, json={"fields": fields}, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code in (201, 200):
                return response.json()
            else:
                console.print(f"[red]Error creating issue: {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Connection Error: {e}[/red]")
            return None

    def edit_issue(self, key, fields):
        url = f"{self.config.jira_url}{self.config.endpoint_issue}/{key}"
        try:
            response = requests.put(url, json={"fields": fields}, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code in (204, 200):
                return True
            else:
                console.print(f"[red]Error editing issue: {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Connection Error: {e}[/red]")
            return False

            return False

    def get_issue(self, key):
        url = f"{self.config.jira_url}{self.config.endpoint_issue}/{key}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                console.print(f"[red]Error fetching issue: {response.status_code}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Connection Error: {e}[/red]")
            return None

    def get_sprint_id(self, sprint_name):
        """
        RESOLVES SPRINT NAME TO ID BY SEARCHING FOR ISSUES IN THAT SPRINT.
        LIMITATION: WRITES ERROR IF SPRINT IS EMPTY.
        """
        jql = f'sprint = "{sprint_name}"'
        issues = self.search_issues(jql, limit=1)
        
        if not issues:
            console.print(f"[yellow]Could not find any issues in sprint '{sprint_name}'. Cannot resolve ID if sprint is empty.[/yellow]")
            return None
            
        # Get sprint field from first issue
        sprints = issues[0]["fields"].get(self.config.field_sprints)
        if not sprints:
            return None
            
        target_id = None
        for spr in sprints:
            # Parse: ...[id=123,name=Name,...]
            if f"name={sprint_name}" in str(spr):
                # Extract ID
                try:
                    # simplistic parse
                    parts = str(spr).split('[')[1].split(']')[0].split(',')
                    for p in parts:
                        if p.startswith('id='):
                            target_id = p.split('=')[1]
                            return int(target_id)
                except:
                    pass
        
        # Fallback: if proper parsing fails but we found issues, usually the last one is active
        # But we really need the ID.
        return target_id

    def search_issues(self, jql, limit=100):
        url = f"{self.config.jira_url}{self.config.endpoint_search}"
        start_at = 0
        all_issues = []
        
        # Fields to fetch
        fields = [
            "key", "summary", "status", "assignee", "created", "resolutiondate", 
            "issuetype", "priority", "project", "fixVersions", "timespent",
            self.config.field_story_points,
            self.config.field_sprints,
            self.config.field_epic_link,
            self.config.field_activity_type,
            self.config.field_root_request,
            self.config.field_parent_link
        ]
        
        fields_param = ",".join(fields)

        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching issues...", total=None)
            
            while True:
                params = {
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": min(limit - len(all_issues), 100),
                    "fields": fields_param
                }

                try:
                    response = requests.get(
                        url, 
                        params=params, 
                        auth=self.auth, 
                        headers=self.headers,
                        timeout=30 # Add timeout for safety
                    )
                    
                    if response.status_code != 200:
                        progress.stop()
                        console.print(f"[red]Error fetching issues: {response.status_code}[/red]")
                        console.print(f"[red]{response.text}[/red]")
                        sys.exit(1)

                    data = response.json()
                    issues = data.get("issues", [])
                    all_issues.extend(issues)
                    
                    progress.update(task, completed=len(all_issues))

                    if len(issues) < params["maxResults"] or len(all_issues) >= limit:
                        break
                    
                    start_at += len(issues)
                    
                except requests.exceptions.RequestException as e:
                    progress.stop()
                    console.print(f"[red]Connection error: {e}[/red]")
                    sys.exit(1)

        return all_issues

class IssueParser:
    """
    Parses raw Jira issue data into a structured format.
    """
    def __init__(self, config):
        self.config = config

    def parse(self, issues):
        parsed_issues = []
        for issue in issues:
            fields = issue.get("fields", {})
            
            # Basic Fields
            key = issue.get("key")
            summary = fields.get("summary")
            status = fields.get("status", {}).get("name")
            
            if self.config.anonymize:
                summary = f"Redacted Summary for {key}"
            assignee = fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
            priority = fields.get("priority", {}).get("name") if fields.get("priority") else "None"
            issue_type = fields.get("issuetype", {}).get("name")
            
            # Custom Fields
            epic_link = fields.get(self.config.field_epic_link)
            story_points = fields.get(self.config.field_story_points)
            
            # Sprint parsing
            sprints = fields.get(self.config.field_sprints)
            sprint_name = ""
            if sprints:
                # Assuming the most recent sprint is relevant or similar logic to original
                # Original script logic: looks for sprint name in a serialized list string or list of objects
                # Getting the last one usually implies "current" or "latest"
                last_sprint = sprints[-1]
                if isinstance(last_sprint, str):
                    # Parse string format: "com.atlassian.greenhopper.service.sprint.Sprint@...[id=...,name=Sprint 51,...]"
                    parts = last_sprint.split(',')
                    for part in parts:
                        if 'name=' in part:
                            sprint_name = part.split('name=')[1]
                            # Clean up trailing bracket if present
                            if sprint_name.endswith(']'):
                                sprint_name = sprint_name[:-1]
                            break
                elif isinstance(last_sprint, dict):
                    sprint_name = last_sprint.get("name", "")
            
            parsed_issues.append({
                "Key": key,
                "Type": issue_type,
                "Summary": summary,
                "Status": status,
                "Priority": priority,
                "Assignee": assignee,
                "Sprint": sprint_name,
                "Points": str(story_points) if story_points is not None else "",
                "Epic Link": str(epic_link) if epic_link else ""
            })
        return parsed_issues

def display_issues(issues):
    """
    Renders a table of issues using Rich.
    """
    table = Table(title=f"Jira Search Results ({len(issues)})")

    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Summary", style="white")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Assignee", style="blue")
    table.add_column("Sprint", style="bold")
    table.add_column("Points", justify="right")
    table.add_column("Epic Link", style="dim")
    
    # Check if any issue has "Epic Summary" to decide if we show the column
    if issues and "Epic Summary" in issues[0]:
        table.add_column("Epic Summary", style="blue")

    for issue in issues:
        row = [
            issue["Key"],
            issue["Type"],
            issue["Summary"],
            issue["Status"],
            issue["Priority"],
            issue["Assignee"],
            issue["Sprint"],
            issue["Points"],
            issue["Epic Link"]
        ]
        if "Epic Summary" in issue:
             row.append(issue["Epic Summary"])
        
        table.add_row(*row)

    console.print(table)

def display_issue_detail(issue_data, client, config):
    """
    Renders detailed view of a single issue.
    """
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.markdown import Markdown
    from rich.text import Text
    
    fields = issue_data.get("fields", {})
    key = issue_data.get("key")
    
    # helper to get safe value
    def g(path, default=""):
        val = fields
        for p in path.split('.'):
            if isinstance(val, dict):
                val = val.get(p, {})
            else:
                return default
        return val if isinstance(val, (str, int, float)) else default

    summary = fields.get("summary", "")
    if config.anonymize:
        summary = f"Redacted Summary for {key}"

    description = fields.get("description")
    if config.anonymize and description:
        description = "Redacted Description"
    
    # Resolve Epic Name if link exists
    epic_link = fields.get(config.field_epic_link)
    epic_name = ""
    if epic_link:
        raw_name = client.get_epic_summary(epic_link)
        epic_name = f"Redacted Epic for {epic_link}" if config.anonymize else raw_name

    # Fix Versions
    fix_versions = ", ".join([v.get("name") for v in fields.get("fixVersions", [])])

    # Assignee
    assignee = fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"

    # Status & Priority
    status = fields.get("status", {}).get("name")
    priority = fields.get("priority", {}).get("name")
    
    # Type
    issue_type = fields.get("issuetype", {}).get("name")
    
    # Points
    points = fields.get(config.field_story_points, "")
    
    # Construct Content
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="cyan", justify="right")
    grid.add_column(style="white")
    
    grid.add_row("Type:", issue_type)
    grid.add_row("Status:", f"[bold green]{status}[/bold green]")
    grid.add_row("Priority:", priority)
    grid.add_row("Assignee:", assignee)
    grid.add_row("Story Points:", str(points) if points is not None else "")
    grid.add_row("Fix Version:", fix_versions)
    grid.add_row("Epic Link:", str(epic_link))
    grid.add_row("Epic Name:", f"[blue]{epic_name}[/blue]")

    console.print(Panel(
        grid,
        title=f"[bold]{key}: {summary}[/bold]",
        subtitle=f"Project: {fields.get('project', {}).get('name')}"
    ))

    if description:
        console.print(Panel(Markdown(description), title="Description"))
    else:
        console.print(Panel("[italic]No description provided.[/italic]", title="Description"))

    # Issue Link
    issue_url = f"{config.jira_url}/browse/{key}"
    console.print(f"\n[bold]Open in Jira:[/bold] [link={issue_url}]{issue_url}[/link]\n")

def main():
    parser = argparse.ArgumentParser(description="Jira CLI - Terminal Client for Jira")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search issues using JQL")
    search_parser.add_argument("--jql", help="JQL Query string", required=False)
    search_parser.add_argument("--limit", type=int, default=50, help="Max results to return")
    search_parser.add_argument("--sort", help="Column to sort by (e.g. status, assignee, priority)", required=False)
    search_parser.add_argument("--epic-name", action="store_true", help="Fetch and show Epic names")
    search_parser.add_argument("--group-by", help="Comma-separated columns to group by (e.g. Status,Assignee)", required=False)
    search_parser.add_argument("--pivot-rows", help="Row field for pivot table", required=False)
    search_parser.add_argument("--pivot-cols", help="Column field for pivot table", required=False)
    search_parser.add_argument("--pivot-values", help="Value field for pivot table (default: Points)", default="Points", required=False)

    # Create Command
    create_parser = subparsers.add_parser("create", help="Create a new issue")
    create_parser.add_argument("--project", required=True, help="Project Key (e.g. PROJ)")
    create_parser.add_argument("--summary", required=True, help="Issue Summary")
    create_parser.add_argument("--type", required=True, help="Issue Type (e.g. Story, Bug)")
    create_parser.add_argument("--description", required=False, help="Issue Description")
    create_parser.add_argument("--assignee", required=False, help="Assignee username")
    create_parser.add_argument("--points", type=float, required=False, help="Story Points")
    create_parser.add_argument("--epic-link", required=False, help="Epic Link Key")
    create_parser.add_argument("--sprint", required=False, help="Sprint Name")

    # Edit Command
    edit_parser = subparsers.add_parser("edit", help="Edit an issue")
    edit_parser.add_argument("key", help="Issue Key (e.g. PROJ-123)")
    edit_parser.add_argument("--summary", required=False, help="New Summary")
    edit_parser.add_argument("--description", required=False, help="New Description")
    edit_parser.add_argument("--type", required=False, help="New Issue Type")
    edit_parser.add_argument("--assignee", required=False, help="New Assignee")
    edit_parser.add_argument("--points", type=float, required=False, help="New Story Points")
    edit_parser.add_argument("--epic-link", required=False, help="New Epic Link")
    edit_parser.add_argument("--sprint", required=False, help="Sprint Name to move ticket to")
    edit_parser.add_argument("--clear-sprint", action="store_true", help="Remove ticket from sprint")
    
    # View Command
    view_parser = subparsers.add_parser("view", help="View issue details")
    view_parser.add_argument("key", help="Issue Key (e.g. PROJ-123)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load Config
    config = ConfigLoader()
    config.validate()

    # Initialize Client
    client = JiraClient(config)
    issue_parser = IssueParser(config)

    if args.command == "search":
        jql = args.jql
        if not jql:
            jql = console.input("[bold yellow]Enter JQL query:[/bold yellow] ")
        
        issues = client.search_issues(jql, limit=args.limit)
        parsed_issues = issue_parser.parse(issues)
        
        if args.sort:
            sort_key = args.sort.lower()
            try:
                parsed_issues.sort(key=lambda x: str(x.get(next(k for k in x.keys() if k.lower() == sort_key), "")).lower())
            except StopIteration:
                console.print(f"[yellow]Warning: Column '{args.sort}' not found. Displaying unsorted.[/yellow]")

        if args.epic_name:
            with Progress() as progress:
                task = progress.add_task("[cyan]Fetching Epic details...", total=len(parsed_issues))
                for issue in parsed_issues:
                    epic_link = issue.get("Epic Link")
                    if epic_link:
                        raw_summary = client.get_epic_summary(epic_link)
                        if config.anonymize:
                            issue["Epic Summary"] = f"Redacted Epic for {epic_link}"
                        else:
                            issue["Epic Summary"] = raw_summary
                    else:
                         issue["Epic Summary"] = ""
                    progress.advance(task)

        if args.group_by:
            df = pd.DataFrame(parsed_issues)
            df['Points'] = pd.to_numeric(df['Points'], errors='coerce').fillna(0)
            
            group_cols = [col.strip() for col in args.group_by.split(',')]
            available_cols = {c.lower(): c for c in df.columns}
            valid_group_cols = []
            for col in group_cols:
                if col.lower() in available_cols:
                    valid_group_cols.append(available_cols[col.lower()])
                else:
                    console.print(f"[yellow]Warning: Column '{col}' not found. Ignoring.[/yellow]")
            
            if valid_group_cols:
                grouped = df.groupby(valid_group_cols).agg(
                    Count=('Key', 'count'),
                    Total_Points=('Points', 'sum')
                ).reset_index()
                grouped = grouped.sort_values(by='Total_Points', ascending=False)
                
                table = Table(title=f"Grouped by {', '.join(valid_group_cols)}")
                for col in valid_group_cols:
                    table.add_column(col, style="cyan")
                table.add_column("Count", justify="right", style="green")
                table.add_column("Total Points", justify="right", style="magenta")
                
                for _, row in grouped.iterrows():
                    table_row = [str(row[col]) for col in valid_group_cols]
                    table_row.append(str(row['Count']))
                    table_row.append(f"{row['Total_Points']:.1f}")
                    table.add_row(*table_row)

                # Grand Totals
                total_count = grouped['Count'].sum()
                total_points = grouped['Total_Points'].sum()
                
                table.add_section()
                total_row = ["Total"] + [""] * (len(valid_group_cols) - 1)
                total_row.append(str(total_count))
                total_row.append(f"{total_points:.1f}")
                table.add_row(*total_row)
                
                console.print(table)
                sys.exit(0)

        if args.pivot_rows and args.pivot_cols:
            df = pd.DataFrame(parsed_issues)
            df['Points'] = pd.to_numeric(df['Points'], errors='coerce').fillna(0)
            
            rows = args.pivot_rows
            cols = args.pivot_cols
            val = args.pivot_values
            
            avail = {c.lower(): c for c in df.columns}
            if rows.lower() not in avail or cols.lower() not in avail:
                 console.print(f"[red]Error: Columns '{rows}' or '{cols}' not found.[/red]")
                 sys.exit(1)
            
            rows = avail[rows.lower()]
            cols = avail[cols.lower()]
            real_val = avail.get(val.lower(), val)
            
            agg = 'sum'
            if real_val == 'Points':
                 agg = 'sum'
            else:
                 agg = 'count'
            
            try:
                pivot = pd.pivot_table(df, index=rows, columns=cols, values=real_val, aggfunc=agg, fill_value=0, margins=True, margins_name='Total')
                title = f"Pivot: {rows} (Rows) x {cols} (Cols) - {agg.title()} of {real_val}"
                table = Table(title=title)
                
                table.add_column(rows, style="cyan")
                for col_name in pivot.columns:
                    table.add_column(str(col_name), justify="right")
                
                for index, row in pivot.iterrows():
                    table_row = [str(index)]
                    for col_name in pivot.columns:
                        try:
                            val = row[col_name]
                            if isinstance(val, (int, float)) and val == 0:
                                val_to_str = ""
                            else:
                                val_to_str = f"{val:.1f}" if isinstance(val, (int, float)) else str(val)
                            table_row.append(val_to_str)
                        except:
                            table_row.append(str(row[col_name]))
                    table.add_row(*table_row)
                    
                console.print(table)
                sys.exit(0)
            except Exception as e:
                console.print(f"[red]Pivot Error: {e}[/red]")
                sys.exit(1)

        display_issues(parsed_issues)

    elif args.command == "create":
        fields = {
            "project": {"key": args.project},
            "summary": args.summary,
            "issuetype": {"name": args.type},
        }
        if args.description:
            fields["description"] = args.description
        if args.assignee:
            fields["assignee"] = {"name": args.assignee}
        if args.points is not None:
             fields[config.field_story_points] = args.points
        if args.epic_link:
             fields[config.field_epic_link] = args.epic_link
        
        if args.sprint:
            sprint_id = client.get_sprint_id(args.sprint)
            if sprint_id:
                # Sprints usually require numeric ID
                fields[config.field_sprints] = sprint_id
            else:
                console.print(f"[red]Aborting create: Could not resolve ID for sprint '{args.sprint}'[/red]")
                sys.exit(1)

        result = client.create_issue(fields)
        if result:
            console.print(f"[green]Issue Created: {result.get('key')} - {result.get('self')}[/green]")

    elif args.command == "edit":
        fields = {}
        if args.summary: fields["summary"] = args.summary
        if args.description: fields["description"] = args.description
        if args.type: fields["issuetype"] = {"name": args.type}
        if args.assignee: fields["assignee"] = {"name": args.assignee}
        if args.points is not None: fields[config.field_story_points] = args.points
        if args.epic_link: fields[config.field_epic_link] = args.epic_link
        
        if args.sprint:
            sprint_id = client.get_sprint_id(args.sprint)
            if sprint_id:
                fields[config.field_sprints] = sprint_id
            else:
                console.print(f"[red]Aborting edit: Could not resolve ID for sprint '{args.sprint}'[/red]")
                sys.exit(1)
        elif args.clear_sprint:
             # To clear a field in Jira, typically set to None/null
             fields[config.field_sprints] = None

        if not fields:
            console.print("[yellow]No fields to update.[/yellow]")
            sys.exit(0)

        success = client.edit_issue(args.key, fields)
        if success:
            console.print(f"[green]Issue {args.key} updated successfully.[/green]")

    elif args.command == "view":
        issue = client.get_issue(args.key)
        if issue:
            display_issue_detail(issue, client, config)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
