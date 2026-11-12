# find-state-machine

Find the state machines an app already has but never declared: the flags,
booleans, status strings, and enums that together encode a lifecycle.

## Use it with a prompt

- `/find-state-machine` finds all of them: "find all of the implicit state
  machines in my app".
- `/find-state-machine checkout` digs into the one behind a flow, model, or
  file: its states and where each lives, every transition and its guard,
  states that nothing names or nothing leaves, and a Mermaid diagram.

How to answer is left to the agent, against the app in front of it.

## Credit

The no-argument prompt is [Steve Ruiz's post](https://x.com/steveruizok/status/2116552016218710389)
of 31 October 2026, used verbatim.
