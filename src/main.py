import os
from jira_handler import JiraHandler

def main():
    # Get the absolute path to the config file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(current_dir), 'config', 'config.yaml')
    
    # Initialize and run the Jira handler
    handler = JiraHandler(config_path)
    handler.run_assignment_loop()

def cloud_function_handler(event, context):
    handler = JiraHandler('config/config.yaml')
    # Run once per trigger instead of continuous loop
    new_issues = handler.get_new_issues()
    for issue in new_issues:
        handler.assign_issue(issue)

if __name__ == "__main__":
    main()
    