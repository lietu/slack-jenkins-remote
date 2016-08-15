# Your token from Slack, used to validate the source of requests
SLACK_TOKEN = ""

# Can't send responses to Slack commands after 30min, consider build
# to have timed out after this many seconds
SLACK_TIMEOUT = 28 * 60

# How to connect your Jenkins server
JENKINS_SERVER = "http://jenkins"
JENKINS_USERNAME = None
JENKINS_PASSWORD = None

# If all Jenkins param names should be uppercased, i.e.
# --branch=default becomes BRANCH=default
JENKINS_UPPERCASE_PARAMS = True

# If you want to run Flask in debug mode
FLASK_DEBUG = False

# If you don't actually want to send requests to Slack
TEST_MODE = True
