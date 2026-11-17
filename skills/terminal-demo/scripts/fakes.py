"""Builds the made-up machine a demo records on. A project's setup.py imports
this, describes its machine, and runs before every take.

    import sys; sys.path.insert(0, "<skill dir>/scripts")
    from fakes import Machine

    m = Machine()                       # $DEMO_ENV, wiped and rebuilt
    m.cmd("acme", '''
    case "$1" in
      list) cat "$DATA/acme-list.json" ;;
      *) unexpected "$@" ;;
    esac''')
    m.data("acme-list.json", [{"name": "widget", "version": "1.2.0"}])
    m.web("api.acme.test", "/v1/latest/widget", {"version": "1.3.0"})
    m.home("projects/shop/acme.lock", "widget 1.2.0\\n")
    m.expect_miss("GET", "api.acme.test", "/v1/latest/retired")
    m.done()

Inside the container the machine is mounted at the same path, so a path
written here is right in both places. env.sh points HOME, PATH and the CA at it.

- m.cmd(name, body) writes a fake command to bin/. It logs each call to
  run/calls.log, and its body's catch-all should call `unexpected "$@"`, so a
  call the fake doesn't know fails loudly and validate.py reports it.
- m.data(name, obj) writes a file fake commands read, as $DATA/<name>.
- m.state(name, text) writes a file a fake command may change during a take,
  as $STATE/<name>; an install that bumps a version writes here.
- m.web(host, path, obj) writes an answer fakeweb serves for
  https://<host><path>. A path ending in / is served from __index. The query
  string is ignored, so one file answers every query to that path.
- m.home(path, text) writes a file under the made-up HOME.
- m.expect_miss(method, host, path) lists a request that is meant to fail,
  such as a resource that is gone on purpose. Any other miss fails validation.
"""
import json
import os
import shutil
import textwrap


class Machine:
    def __init__(self, root=None):
        demo = os.path.basename(os.getcwd())
        self.root = root or os.environ.get("DEMO_ENV", f"/tmp/terminal-demo/{demo}")
        shutil.rmtree(self.root, ignore_errors=True)
        for d in ("bin", "data", "state", "web", "home", "run"):
            os.makedirs(os.path.join(self.root, d))
        self.misses = []

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def write(self, rel, content, mode=None):
        p = self.path(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not isinstance(content, (str, bytes)):
            content = json.dumps(content, indent=2)
        with open(p, "wb" if isinstance(content, bytes) else "w") as f:
            f.write(content)
        if mode:
            os.chmod(p, mode)
        return p

    def cmd(self, name, body):
        prelude = (f"#!/bin/bash\nDATA={self.path('data')}\nSTATE={self.path('state')}\n"
                   f"echo \"{name} $*\" >> {self.path('run', 'calls.log')}\n"
                   f"unexpected() {{ echo \"{name}: unexpected $*\" | tee -a {self.path('run', 'calls.log')} >&2; exit 2; }}\n")
        return self.write(f"bin/{name}", prelude + textwrap.dedent(body).strip() + "\n", 0o755)

    def data(self, name, content):
        return self.write(f"data/{name}", content)

    def state(self, name, content):
        return self.write(f"state/{name}", content)

    def web(self, host, path, content):
        if path.endswith("/"):
            path += "__index"
        if not isinstance(content, (str, bytes)):
            content = json.dumps(content)
        return self.write(f"web/{host}/{path.lstrip('/')}", content)

    def home(self, rel, content, mode=None):
        return self.write(f"home/{rel}", content, mode)

    def expect_miss(self, method, host, path):
        self.misses.append(f"MISS {method} {host}{path}")

    def done(self):
        self.write("run/expected-misses.txt", "".join(m + "\n" for m in self.misses))
        open(self.path("run", "calls.log"), "w").close()
        hosts = sorted(os.listdir(self.path("web")))
        print(f"made-up machine at {self.root}: {len(os.listdir(self.path('bin')))} commands, "
              f"{sum(len(f) for _, _, f in os.walk(self.path('web')))} web answers on {len(hosts)} hosts")
