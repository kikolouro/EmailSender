#!/bin/bash
source .env
docker image rm -f emailsender:$APPVERSION
