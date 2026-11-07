---
name: use-siyuan
description: "Use when the user works with SiYuan or their notes: mentioning SiYuan, the `siyuan` command, or a SiYuan workspace; asking to add, append, write, note, or save something to their notes or notebook; asking what they wrote or to find an existing note; adding to a daily note or journal; exporting, importing, backing up, or syncing notes, documents, or a workspace; or referencing a notebook, document, block, tag, database, asset, or template. Also matches Vietnamese: \"ghi chú\", \"sổ tay\", \"thêm vào ghi chú\", \"nhật ký\"."
---

# Use SiYuan CLI

`siyuan` is the SiYuan kernel binary (v3.8.3) shipped with the desktop app. It
exposes the whole SiYuan data model as subcommands and works directly on
workspace files. No running kernel or HTTP server is needed; `siyuan serve` is
only for starting the HTTP API server.

## Workspace selection (read this first)

Data commands (`notebook`, `document`, `block`, `search`, `sql`, `file`, `tag`,
`database`, ...) default to `$HOME/SiYuan`. If that path is not a workspace you
get `Error: directory not found: /Users/<you>/SiYuan`.

```bash
siyuan workspace list                       # registered workspaces
siyuan -w /path/to/workspace notebook list  # target one explicitly
```

- `-w` is global and works before or after the subcommand.
- It registers the path in `~/.config/siyuan/workspace.json` as a side effect,
  so do not point it at throwaway copies.
- `workspace list` / `workspace info` ignore `-w`; they read the registry.

## Mental model

`notebook` > `document` (a block with `type=doc`) > child `block`s. Block IDs
look like `20240101000000-abcdefg`; a document's ID is its `root_id`. Content
input is always Markdown via `--data <markdown>` or `--file <path>`
(`-` reads stdin).

## Core workflows

Discover IDs first, then act on them.

```bash
# Locate
siyuan -w "$WS" notebook list
siyuan -w "$WS" document search "onboarding"           # titles + hPath
siyuan -w "$WS" document list --notebook <nbID>
siyuan -w "$WS" outline get --id <docID>               # heading tree

# Read
siyuan -w "$WS" block kramdown --id <docID>            # Markdown + IAL ids
siyuan -w "$WS" export md --id <docID>                 # clean Markdown
siyuan -w "$WS" block children --id <blockID>
siyuan -w "$WS" attr get --id <blockID>

# Write
siyuan -w "$WS" document create --notebook <nbID> --title "T" --markdown "# Hi"
siyuan -w "$WS" block append --parent <docID> --data "- new bullet"
siyuan -w "$WS" block update --id <blockID> --data "replacement"
siyuan -w "$WS" attr set --id <docID> --attr icon=1f4ca --attr tags=work

# Query
siyuan -w "$WS" search "keyword"
siyuan -w "$WS" sql "select id,type from blocks limit 20"
siyuan -w "$WS" ref backlinks --id <blockID>
```

`block append`/`prepend` add a sibling at the end or start of the parent;
`block insert --previous <siblingID>` places precisely. `document create` takes
`--path` (internal parent path, default `/`); `document list`, `document move`,
and `import` also accept `--hpath` (human path like `/Work/Projects`).

## Output and safety

- Default output is a table; pass `-f json` to parse. A few commands print a
  bare ID and ignore `-f` (`notebook create`, `document create`, `block append`).
- `--dry-run` is global: validate and print without changing anything. Use it
  before destructive calls.
- Never hand-edit `.sy` files (kernel JSON). Use `block`/`document` commands;
  `file write` is for conf, plugins, and snippets.

## Gotchas

- `search` table rows embed `<mark>` tags; JSON keeps `content` highlighted and
  `markdown` clean.
- `sql` defaults to 100 rows (`-l` to raise); `blocks` is the main table.
- `file` paths are workspace-relative (`data/...`, `conf/conf.json`); a leading
  `/` or `.` fails with `path escapes workspace`.
- `block update --lock-type` refuses updates that would change the block type.
- `dailynote append/create/prepend` require `--notebook`.

## Full command catalog

`references/commands.md` lists every group and subcommand with signatures.
`siyuan --help` lists the command groups; `siyuan <group> --help` lists the rest.
