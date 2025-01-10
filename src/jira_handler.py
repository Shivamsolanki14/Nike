from jira import JIRA
import logging
import yaml
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/jira_auto_assign.log', mode='a')
    ]
)

class JiraHandler:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.jira = self._initialize_jira()
        self.last_check_time = datetime.now() - timedelta(minutes=5)

    def _load_config(self, config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

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
            self.jira.assign_issue(
                issue,
                self.config['assignment']['assignee_email']
            )
            logging.info(
                f"Successfully assigned issue {issue.key} to "
                f"{self.config['assignment']['assignee_email']}"
            )
            return True
        except Exception as e:
            logging.error(f"Error assigning issue {issue.key}: {str(e)}")
            return False

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