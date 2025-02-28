import os
from jira import JIRA
import logging
import yaml
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class JiraHandler:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.jira = self._initialize_jira()
        self.last_check_time = datetime.now() - timedelta(minutes=5)

    def _load_config(self, config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            
        # Override with environment variables if available
        if os.getenv('JIRA_SERVER'):
            config['jira']['server'] = os.getenv('JIRA_SERVER')
        if os.getenv('JIRA_EMAIL'):
            config['jira']['email'] = os.getenv('JIRA_EMAIL')
        if os.getenv('JIRA_API_TOKEN'):
            config['jira']['api_token'] = os.getenv('JIRA_API_TOKEN')
        if os.getenv('ASSIGNEE_EMAIL'):
            config['assignment']['assignee_email'] = os.getenv('ASSIGNEE_EMAIL')
        if os.getenv('PROJECT_KEY'):
            config['assignment']['project_key'] = os.getenv('PROJECT_KEY')
            
        return config

    def _initialize_jira(self):
        try:
            return JIRA(
                server=self.config['jira']['server'],
                basic_auth=(
                    self.config['jira']['email'],
                    self.config['jira']['api_token']
                )
            )
        except Exception as e:
            logging.error(f"Failed to initialize JIRA: {str(e)}")
            raise

    def get_new_issues(self):
        try:
            jql = (
                f"project = {self.config['assignment']['project_key']} "
                f"AND created >= '{self.last_check_time.strftime('%Y-%m-%d %H:%M')}' "
                "AND assignee is EMPTY"
            )
            
            issues = self.jira.search_issues(jql)
            self.last_check_time = datetime.now()
            return issues
        except Exception as e:
            logging.error(f"Error fetching issues: {str(e)}")
            return []

    def assign_issue(self, issue):
        try:
            issue_labels = set(issue.fields.labels)
            target_labels = {"dynatrace", "tracing"}

            if target_labels.intersection(issue_labels):
                self.jira.assign_issue(
                    issue,
                    self.config['assignment']['assignee_email']
                )
                logging.info(
                    f"Successfully assigned issue {issue.key} to "
                    f"{self.config['assignment']['assignee_email']}"
                )

                # **NEW: Change status to "Work In Progress"**
                self.transition_issue_to_wip(issue)

                return True
            else:
                logging.info(f"Issue {issue.key} does not match the target labels.")
                return False
        except Exception as e:
            logging.error(f"Error assigning issue {issue.key}: {str(e)}")
            return False

    def transition_issue_to_wip(self, issue):
        """Find the correct transition and move issue to 'Work In Progress'."""
        try:
            # Get the current status of the issue
            current_status = issue.fields.status.name.lower()
            logging.info(f"Issue {issue.key} is currently in status: {current_status}")

            # Fetch available transitions
            transitions = self.jira.transitions(issue)

            # Log all available transitions
            for transition in transitions:
                logging.info(f"Transition available: {transition['id']} - {transition['name']}")

            wip_transition_id = None

            for transition in transitions:
                # Check if "Work In Progress" is available
                if transition['name'].lower() in ["work in progress", "in progress"]:
                    wip_transition_id = transition['id']
                    break

            if wip_transition_id:
                self.jira.transition_issue(issue, wip_transition_id)
                logging.info(f"Issue {issue.key} transitioned to 'Work In Progress'")
            else:
                logging.warning(f"No direct 'Work In Progress' transition found for {issue.key}. Trying 'Investigate' first.")

                # If "Work In Progress" is not available, check for "Investigate"
                investigate_transition_id = None
                for transition in transitions:
                    if transition['name'].lower() == "investigate":
                        investigate_transition_id = transition['id']
                        break
                
                # First, move to "Investigate" if required
                if investigate_transition_id:
                    self.jira.transition_issue(issue, investigate_transition_id)
                    logging.info(f"Issue {issue.key} transitioned to 'Investigate'")

                    # Fetch transitions again after moving to "Investigate"
                    time.sleep(2)  # Small delay to allow Jira to update
                    transitions = self.jira.transitions(issue)
                    
                    # Now, check if "Work In Progress" is available
                    for transition in transitions:
                        if transition['name'].lower() in ["work in progress", "in progress"]:
                            wip_transition_id = transition['id']
                            break

                    if wip_transition_id:
                        self.jira.transition_issue(issue, wip_transition_id)
                        logging.info(f"Issue {issue.key} finally transitioned to 'Work In Progress'")
                    else:
                        logging.warning(f"Still no 'Work In Progress' transition found for {issue.key}")
                else:
                    logging.warning(f"No 'Investigate' transition found for {issue.key}")
        except Exception as e:
            logging.error(f"Error transitioning issue {issue.key}: {str(e)}")


    def run_assignment_loop(self):
        while True:  # This ensures 24/7 operation
            try:
                new_issues = self.get_new_issues()
                for issue in new_issues:
                    self.assign_issue(issue)
                
                time.sleep(self.config['polling']['interval_seconds'])
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying on error 

    def notify_error(self, error_message):
        print(f"::error::{error_message}")
