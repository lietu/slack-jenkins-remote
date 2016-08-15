#!/usr/bin/env bash

TOKEN=""
JOB="backend-tests"
PARAMS="--branch=feature/jenkins_changes"

DATA="token=$TOKEN&team_id=T0001&team_domain=example&channel_id=C2147483705&channel_name=test&user_id=U2147483697&user_name=Steve&command=/build&text=$JOB $PARAMS&response_url=http://127.0.0.1/not-real"

curl -X POST -d "$DATA" http://127.0.0.1:5000
