"""Builds the made-up machine for this demo. Run it before every take: a take
can change it (an install bumps a version), and caches it seeds can expire.
Every name, version, URL and person here is made up."""
import os
import sys

sys.path.insert(0, os.path.expanduser("<skill dir>/scripts"))
from fakes import Machine

m = Machine()

# The commands the app runs, each answering only the calls this demo makes.
m.cmd("acme-registry", '''
case "$1" in
  list) cat "$DATA/list.json" ;;
  *) unexpected "$@" ;;
esac''')
m.data("list.json", [{"name": "widget", "version": "1.2.0"}])

# The web answers, under the real hostnames the app asks.
m.web("api.acme.test", "/v1/latest/widget", {"version": "1.3.0"})

# Files the app reads from HOME: config, caches, a project folder.
m.home(".config/acme/config.toml", 'theme = "dark"\n')

m.done()
