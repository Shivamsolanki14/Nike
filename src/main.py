import os
from jira_handler import JiraHandler

def main():
    # Get the absolute path to the config file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_dir), 'config', 'config.yaml')
    # config_path = os.path.abspath(os.path.join(current_dir, '../config/config.yaml'))  # Adjusted path
    
    # Initialize the Jira handler
    handler = JiraHandler(config_path)
    
    # Run once
    new_issues = handler.get_new_issues()
    for issue in new_issues:
        handler.assign_issue(issue)

if __name__ == "__main__":
    main()
