#!/bin/bash
# Records one take from the demo folder and keeps its logs beside it.
# The take's name comes from the tape's Output line, and an existing take is
# never overwritten: bump the name in the tape for each recording.
#
# Usage: record.sh <tape>       (run the project's setup first)
set -euo pipefail
tape=$1
here=$(cd "$(dirname "$0")" && pwd)
out=$(sed -n 's/^Output[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}[[:space:]]*$/\1/p' "$tape" | head -1)
case "$out" in
	takes/*.mp4) ;;
	*) echo "the tape's Output must be takes/<name>.mp4, got '$out'" >&2; exit 1 ;;
esac
take=$(basename "$out" .mp4)
[ -e "$out" ] && { echo "$out exists: bump the take name in $tape" >&2; exit 1; }
export DEMO_ENV=${DEMO_ENV:-/tmp/terminal-demo/$(basename "$(pwd)")}
[ -d "$DEMO_ENV" ] || { echo "no made-up machine at $DEMO_ENV: run the setup first" >&2; exit 1; }
mkdir -p takes runs "runs/$take"
"$here/run.sh" "vhs $tape" > "runs/$take/vhs.log" 2>&1 || { tail -5 "runs/$take/vhs.log" >&2; exit 1; }
cp -R "$DEMO_ENV/run/." "runs/$take/"
echo "takes/$take.mp4, logs in runs/$take"
