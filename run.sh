#!/usr/bin/env bash
#
# Starts up the application
#
# If you don't want to setup the virtual environment in another directory
# give the path as an argument, e.g.:
#
#   run.sh $HOME/sjr-venv
#

setup_virtualenv() {
    VENV_PATH="$1"
    if [[ "$VENV_PATH" == "" ]]; then
        VENV_PATH=".venv"
    fi

    if [[ ! -d "$VENV_PATH" ]]; then
        virtualenv "$VENV_PATH"
    fi

    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt
}

# Set up virtualenv if possible
if [[ "$(which virtualenv)" != "" ]]; then
    setup_virtualenv "$1"
else
    echo -n "No virtualenv detected in PATH, you'll have to deal with "
    echo "dependencies yourself."
fi

exec FLASK_APP=start.py python -m flask run
