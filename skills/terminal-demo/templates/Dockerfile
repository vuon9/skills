# The project's recording image: the skill's image plus the app under test.
# Build: docker build -t <app>-demo:1 . ; then TD_IMAGE=<app>-demo:1 for run.sh and record.sh.
FROM terminal-demo:1
# An app from the distribution:
# RUN apt-get update && apt-get install -y --no-install-recommends <app> && rm -rf /var/lib/apt/lists/*
# Or a static binary built for linux on the container's architecture, mounted
# through the made-up machine's bin/ by setup.py instead of copied here.
