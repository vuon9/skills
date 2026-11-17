# The made-up machine

Everything the app can see during a take lives in `$DEMO_ENV` (default
`/tmp/terminal-demo/<demo folder name>`), built fresh by the project's
`setup.py` before every take. Inside the container it is mounted at the same
path, so a path written by setup is right in both places.

| Folder | What lives there |
|---|---|
| `bin/` | fake commands, first on PATH |
| `data/` | files the fake commands read (`$DATA`) |
| `state/` | files a take changes, such as a version an install bumps (`$STATE`) |
| `web/<host>/<path>` | the answers fakeweb serves for `https://<host><path>` |
| `home/` | the made-up HOME: config, caches, a project folder |
| `run/` | the take's logs: keys, timing, fakeweb hits and misses, fake calls |

## Find what the app touches

Before faking anything, list it from the app's code, not from memory:

- every command it runs (search for exec or spawn calls) and the exact
  arguments of each;
- every host it asks (search for `https://`), including mirrors, token
  endpoints and fallbacks;
- every file it reads at startup: config, caches, lock files, history.

Then record one take and read `run/fakeweb.log` and `run/calls.log`: a MISS or
an `unexpected` call is something you missed. Do it again on every new take,
since a new scene may reach a new endpoint.

## Fake commands

Answer only the calls the demo makes, and end with `unexpected "$@"`, so a call
you didn't plan fails loudly and `validate.py` reports it:

```python
m.cmd("acme", '''
case "$1 $2" in
  "list --json") cat "$DATA/list.json" ;;
  "install --yes") echo "installing $3"; sleep 0.8; echo "$3" > "$STATE/installed" ;;
  *) unexpected "$@" ;;
esac''')
```

- Mirror the real tool's output format exactly, from its docs or a captured
  run, with made-up names in it. Tests in the app's repo often hold fixtures of
  the right shape.
- Make slow steps a little slow (`sleep 0.5`), so a spinner or a progress popup
  is visible.
- An action that changes the machine writes to `$STATE`, and the listing reads
  it, so the screen shows the change after it.
- A command that answers differently by its flags (a search with two modes)
  needs a branch per flag, or results show twice.

## Web answers

`m.web(host, path, obj)` writes JSON (or raw bytes) that fakeweb serves over
HTTPS under the real hostname, with a CA that `env.sh` trusts.

- The query string is ignored: one file answers every query to that path.
- A registry or API whose answers carry digests or checksums: compute them in
  setup.py from the exact bytes you write, so "fresh" and "changed" states come
  out as intended.
- A request that should fail on purpose (a thing that is gone): list it with
  `m.expect_miss(method, host, path)`. Every other miss fails validation.
- An app with its own CA list (Node, Java, Python's `certifi`) needs its own
  variable in `env.sh` pointing at `/tmp/fakeca.pem`.

## Caches the app trusts

When the app caches answers on disk (security results, metadata), seeding a
fresh cache can stand in for a whole service. Match the cache's format version
exactly, and seed it from the app's own listing of the made-up machine where
possible, so its keys can't drift from what the app looks up.

## Real names

Keep public names the app needs to work (a language runtime, a base image an
end-of-life check knows). Everything else is invented: package names,
versions, repositories, hosts, people, paths. Put real identifiers (your name,
email, hostname, org, internal hosts) in the deny list, outside the demo folder.
