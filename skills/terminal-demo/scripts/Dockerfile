# The recording image: VHS, tmux for the subtitle marker, fakeweb for made-up
# web answers, and the kit that runs inside. A project adds its app with its own
# Dockerfile that starts FROM this image.
FROM golang:1.24-alpine AS fakeweb
WORKDIR /src
COPY fakeweb/ .
RUN CGO_ENABLED=0 go build -o /fakeweb .

FROM ghcr.io/charmbracelet/vhs:v0.12.1
RUN apt-get update && apt-get install -y --no-install-recommends tmux && rm -rf /var/lib/apt/lists/*
COPY --from=fakeweb /fakeweb /usr/local/bin/fakeweb
COPY tmux.conf timeline.py marker.py /opt/terminal-demo/
