import json
import time
from datetime import timedelta
from threading import Thread
import requests

from flask import Flask, request
from jenkinsapi.custom_exceptions import JenkinsAPIException
from requests import HTTPError

from sjr.jenkins import Jenkins, JenkinsError
from sjr.utils import format_timedelta, format_params
import settings

app = Flask(__name__)
logger = app.logger


def validate_slack_token(token):
    """
    Validate that the token we got from Slack seems valid

    :param str token:
    :return bool:
    """
    if token == settings.SLACK_TOKEN:
        return True
    return False


def validate_data(data):
    """
    Validate that the request from Slack contains all the data we need

    :param dict data:
    :return bool:
    """
    if not data.get("response_url"):
        return False
    if not data.get("token"):
        return False
    if not data.get("command"):
        return False
    if not data.get("user_name"):
        return False
    if not data.get("channel_name"):
        return False
    return True


def get_user_info(data, channel=False):
    """
    Get calling user's information in human readable format from request data

    :param dict data:
    :param bool channel:
    :return str:
    """
    if channel:
        return "{} in {}".format(
            data.get("user_name"),
            data.get("channel_name")
        )

    return data.get("user_name")


def send_response(data, response):
    """
    Send command response to Slack

    :param dict data:
    :param dict response:
    """
    url = data.get("response_url")
    res_json = json.dumps(response, indent=2, sort_keys=True)

    if settings.TEST_MODE:
        logger.warn("TEST MODE! {} -> {}".format(url, res_json))
    else:
        logger.warn("{} -> {}".format(url, res_json))

        headers = {
            "Content-Type": "application/json"
        }

        r = requests.post(
            data.get("response_url"),
            data=res_json,
            headers=headers
        )

        logger.info("Slack responded with status {}".format(
            r.status_code
        ))

        logger.info("Slack response was: {}".format(
            r.content
        ))


def get_command(data):
    """
    Figure out what is the command being run from request data

    :param dict data:
    :return str:
    """
    return data.get("command")


def get_args(data):
    """
    Get the command arguments from request data
    :param dict data:
    :return string[]:
    """
    return data.get("text").split(" ")


def help(command):
    """
    Get the help text

    :param str command:
    :return str:
    """
    jenkins = Jenkins()
    jobs = jenkins.get_supported_jobs()

    help_text = """Trigger Jenkins builds

`{command} help` - Show this help
`{command} JOB` - Build _JOB_ on Jenkins
`{command} JOB --PARAM=value` - Build _JOB_ on Jenkins passing PARAM=value argument

*Supported jobs*:
""".format(command=command)

    for job in jobs:
        help_text += " - `{}`\n".format(job)

    response = {
        "response_type": "ephemeral",
        "text": "How to use {}".format(command),
        "attachments": [{
            "text": help_text,
            "mrkdwn_in": ["text"]
        }]
    }
    return json.dumps(response, indent=2, sort_keys=True)


def check_help(data):
    """
    Check if the user is should be given help with the command

    :param dict data:
    :return bool:
    """
    args = get_args(data)
    if len(args) == 0:
        return True
    if args[0] == "help":
        return True
    return False


def parse_params(args):
    """
    Parse given arguments for job name and params

    :param string[] args:
    :return str, dict:
    """
    job = args[0]
    params = {}
    for arg in args[1:]:
        if arg[:2] == "--":
            name, value = arg[2:].split("=")

            if settings.JENKINS_UPPERCASE_PARAMS:
                name = name.upper()

            params[name] = value

    return job, params


def block_until_build(data, qi, delay=5):
    """
    Wait until the job has started building

    :param dict data:
    :param qi:
    :param int delay:
    :rtype jenkinsapi.build.Build:
    """
    name, _ = parse_params(get_args(data))
    logger.info("Waiting for {} to start building".format(name))
    while True:
        try:
            qi.poll()
            return qi.get_build()
        except (JenkinsAPIException, HTTPError):
            logger.debug("Waiting for {} to start...".format(name))
            time.sleep(delay)


def build_requested(data):
    """
    Send an update saying the build has been requested
    :param dict data:
    :param timedelta eta:
    """
    name, params = parse_params(get_args(data))
    response = {
        "response_type": "in_channel",
        "attachments": [
            {
                "color": "#36a64f",
                "title": "{} requested build of {}".format(
                    get_user_info(data),
                    name
                ),
                "title_link": settings.JENKINS_SERVER,
                "text": "Starting to build {} ({}).".format(
                    name,
                    format_params(params),
                ),
                "mrkdwn_in": ["text"],
            }
        ]
    }

    send_response(data, response)


def build_started(data, eta):
    """
    Send an update saying the build has started
    :param dict data:
    :param timedelta eta:
    """
    name, params = parse_params(get_args(data))
    response = {
        "response_type": "in_channel",
        "attachments": [
            {
                "color": "#36a64f",
                "title": "Started building {}".format(name),
                "title_link": settings.JENKINS_SERVER,
                "text": "Jenkins is now building {} ({}). ETA in {}".format(
                    name,
                    format_params(params),
                    format_timedelta(eta)
                ),
                "mrkdwn_in": ["text"],
            }
        ]
    }

    send_response(data, response)


def build_completed(data, build):
    """
    Send an update saying the build has completed
    :param dict data:
    :param timedelta eta:
    """

    name, params = parse_params(get_args(data))
    status = (build.get_status() == "SUCCESS")

    response = {
        "response_type": "in_channel",
        "attachments": [
            {
                "color": "#36a64f" if status else "#d50200",
                "title": "Built {}, result was a {}".format(
                    name,
                    "SUCCESS" if status else "FAILURE"
                ),
                "title_link": build.get_result_url(),
                "text": "Jenkins built {} ({}) in {}".format(
                    name,
                    format_params(params),
                    format_timedelta(build.get_duration())
                ),
                "mrkdwn_in": ["text"],
            }
        ]
    }

    send_response(data, response)

    if not status:
        console = build.get_console()
        response = {
            "response_type": "in_channel",
            "text": console,
            "mrkdwn": False,
        }
        send_response(data, response)


def job_not_found(data):
    """
    Send an update saying the build has completed
    :param dict data:
    :param timedelta eta:
    """

    name, _ = parse_params(get_args(data))
    response = {
        "response_type": "ephemeral",
        "text": "Job {} not found.".format(name)
    }

    send_response(data, response)


def _wrap_build(data):
    """
    Wrapping the core logic for the thread so we log exceptions

    :param dict data:
    """
    try:
        build(data)
    except:
        logger.exception("Caught exception")


def build(data):
    """
    Process a build request
    :param dict data:
    """
    req_start = time.time()

    args = get_args(data)
    name, params = parse_params(args)

    logger.info("Got request to build {} from {}".format(
        name,
        get_user_info(data, True)
    ))

    # Send notification about the build being requested
    build_requested(data)

    # Ask Jenkins to start a build for this
    server = Jenkins()
    try:
        eta, qi = server.build(name, params)
    except JenkinsError:
        job_not_found(data)
        return

    # Wait until the build actually starts
    build = block_until_build(data, qi)
    start = time.time()

    # Send notification about the build starting
    build_started(data, eta)

    # Wait for the build to complete, and send some ETA updates while at it
    last_message = time.time()
    orig_eta = eta
    while build.is_running():
        now = time.time()
        elapsed = now - last_message
        total_elapsed = now - start
        eta = orig_eta - timedelta(seconds=total_elapsed)

        logger.debug("{:.3f}s elapsed of {}, ETA in {}".format(
            total_elapsed, name, format_timedelta(eta)
        ))

        # TODO: Enable if there is a way to update messages
        # instead of just appending new ones...
        # if elapsed > 30:
        #             build_started(data, eta)
        #    last_message = now

        time.sleep(5)

        # Check if the request has exceeded the Slack response time
        req_elapsed = now - req_start
        if req_elapsed > settings.SLACK_TIMEOUT:
            logger.warn("Build for {} exceeded timeout".format(name))
            return

        build.poll()

    # Build completed, hurrah
    build_completed(data, build)


@app.route("/", methods=["GET"])
def ssl_check():
    """
    Slack will periodically send GET requests to check that the SSL cert
    validates ok. We should just respond with 200 OK as soon as possible.

    https://api.slack.com/slash-commands#ssl
    """
    return "All ok, mm'kay."


@app.route('/', methods=["POST"])
def call():
    """
    Normal command request, possibly from Slack.

    Should respond with 200 OK if the command was successfully received.
    """

    data = dict(request.form)
    if not validate_data(data):
        return "Invalid data", 400

    # Form data to dict() -thing for some reason turns everything into lists
    for key in data:
        data[key] = data[key][0]

    if not validate_slack_token(data.get("token")):
        logger.info("Request failed token validation")
        return "Invalid token", 401

    if check_help(data):
        logger.info("Sending help to {}".format(get_user_info(data, True)))
        headers = {
            "Content-Type": "application/json"
        }
        return help(get_command(data)), 200, headers

    # Looks like a build request, do that in a thread so we can respond with
    # 200 OK quickly. Builds tend to take a while...
    t = Thread(target=_wrap_build, args=[data])
    t.daemon = True
    t.start()

    args = get_args(data)
    return "Gotcha, trying to build {}.".format(
        args[0]
    )
