# statechart

Check a model of how something moves between states (a product flow, a
protocol, a service) and draw it as a Mermaid statechart in your words. Each
rule you agree to becomes an invariant; the report marks the states that
break one and gives the shortest path to each.

## Use it with a prompt

- `/statechart the checkout flow, payment can time out and be retried` -> a
  chart of the flow and the shortest path to any broken rule
- "Show this race as a path through states" -> the bug as numbered steps
- Reading the result of an `invariant-check` that uses TLA+

You judge the rules and the chart. The agent writes the TLA+ model and the
labels, in a scratch folder outside the repo.

## Prerequisites

- Node 22.18+ (or 23.6+), Bun 1.1.5+, or Deno 2+ to run the bundled runner.
  The runner is TypeScript, but it only drives the checker; your project can
  be in any language.
- [mise](https://mise.jdx.dev). The first run uses it to fetch a pinned TLC
  and Java, so it needs the network once.
- Optional: the `pele` npm package, to render a chart as SVG
  (`references/render.md`).

## Relationship

`invariant-check` sets up and reruns formal checks; when one is a TLA+ model,
its results are read here.

## Source

Copied from
[cursor/plugins](https://github.com/cursor/plugins/tree/main/harness/pstack/claude-code/skills/statechart)
(pstack, by Lauren Tan). Edited: the description starts with "Use when" and
the skill can be loaded by an agent, so `invariant-check` and generated check
skills can read their results with it; the upstream test fixtures are left
out.
