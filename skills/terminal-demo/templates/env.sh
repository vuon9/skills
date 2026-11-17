# Sourced inside the container, by the tape and by every tmux shell: the app
# sees only the made-up machine. Add the app's own config variables here.
export HOME=$DEMO_ENV/home
export PATH=$DEMO_ENV/bin:$HOME/bin:/usr/local/bin:/usr/bin:/bin
unset XDG_CONFIG_HOME XDG_CACHE_HOME XDG_STATE_HOME XDG_DATA_HOME HTTPS_PROXY HTTP_PROXY GITHUB_TOKEN GH_TOKEN
# fakeweb's CA, so its answers under the real hostnames are trusted. Apps that
# carry their own CA list need their own variable (NODE_EXTRA_CA_CERTS, ...).
export SSL_CERT_FILE=/tmp/fakeca.pem
export COLORTERM=truecolor
# Without a UTF-8 locale tmux draws every emoji and wide sign as _.
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export PS1='$ '
cd "$HOME"
