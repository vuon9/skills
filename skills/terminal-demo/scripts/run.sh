#!/bin/bash
# Runs a command inside the recording container, from the demo folder.
# The demo folder is /vhs inside. The made-up machine ($DEMO_ENV) is mounted at
# the same path, and fakeweb serves $DEMO_ENV/web under the real hostnames.
#
# Usage: run.sh '<command>'     e.g. run.sh 'vhs demo.tape'
# DEMO_ENV  the made-up machine, default /tmp/terminal-demo/<demo folder name>
# TD_IMAGE  the image, default terminal-demo:1 (or a project image FROM it)
set -euo pipefail
demo=$(pwd)
export DEMO_ENV=${DEMO_ENV:-/tmp/terminal-demo/$(basename "$demo")}
image=${TD_IMAGE:-terminal-demo:1}
hosts=()
if [ -d "$DEMO_ENV/web" ]; then
	for h in $(ls "$DEMO_ENV/web"); do
		hosts+=(--add-host "$h:127.0.0.1")
	done
fi
mkdir -p "$DEMO_ENV/run"
exec docker run --rm "${hosts[@]}" -e DEMO_ENV \
	-v "$demo:/vhs" -v "$DEMO_ENV:$DEMO_ENV" \
	--entrypoint bash "$image" \
	-c "if [ -d $DEMO_ENV/web ]; then fakeweb $DEMO_ENV/web /tmp/fakeca.pem $DEMO_ENV/run/fakeweb.log 2>>$DEMO_ENV/run/fakeweb.err & sleep 1; fi; cd /vhs && $1"
