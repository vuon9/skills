---
name: walk-me
description: "Use when the user wants to work through something one item at a time instead of all at once: questions other people sent them, a problem or black box to break down into questions, or an interview where the agent asks them questions to understand their situation. Orders the items, digs up the evidence for each in a subagent, and waits for the user between items. Built for someone still new to the codebase."
disable-model-invocation: true
---

# Walk me

The user has something to work through and doesn't want it all at once. It may be a pile of questions from teammates, a problem they can't see into yet, or a situation you need to understand. They are still new to the codebase. Take one item at a time, ground each in evidence, and wait for them between items. You are a coach, not a ghostwriter. You draft and they send. Never post anything yourself.

## Arguments

`$ARGUMENTS` is an optional output word, then optional material.

- **Output.** The first word counts as the output only when it names a format or a place, such as `md`, `file`, `html`, `artifact`, `doc`, `notes` or `chat`. Any such word works. Produce that output at the end with whatever this session has, and if it can't, say so and offer the closest option. With no output word, ask where the result should go once the work is done.
- **Material.** Everything after the output word. Pasted questions, a problem description, a doc, or links to tickets, threads or PRs, which you open with the session's tools.

## Modes

Pick the mode from the material.

- **Answer.** Questions other people sent the user. Each item is one question, with who asks, what they want in plain words, and where it came from. Merge duplicates and follow-ups in the same thread.
- **Break down.** A problem, a black box, or something that doesn't add up. Each item is a question that fills in part of the picture once answered. The goal is the user's understanding lined up with what is true. It questions the problem, not the user's plan.
- **Interview.** You need to understand the user's situation or view. Each item is a question you ask them.

Order the items so each answer helps with the next. Keep items about the same ticket, topic or part of the code together, and put an item another one depends on first. In Answer mode, sort the rest by urgency: a blocker, a deadline, how long someone has waited.

## 1. Start

With material, skip the gate. Show the numbered list with the mode and one line on why it is in this order, then start item 1 in the same reply. The user can reorder, merge or drop items at any time.

With no material, read the turns before this one and propose what to work on:

- **Topic.** One line.
- **What happened.** A few lines on the recent turns you based it on.
- **Mode and items.** The mode, and the items in order.
- **Output.** The output word, if one was given.

Then stop. Start when the user says go, and fix whatever they correct. If it isn't what they want, ask what they want to work through, and stop.

## 2. One item at a time

Work on the current item only.

**Answer.**

- What they're asking. The question in plain words, why the person is probably asking, and the background from the ticket or thread. Explain any term, module or acronym that someone new to this codebase may not know.
- Where the answer lives. The files, functions, docs, tickets, PRs or commits that settle it, each with one line on why it matters, cited as `path:line` or a link.
- A suggested answer, short and plain, as the user could send it. Say how sure you are, what you could not prove, and who might know the rest.

**Break down.**

- The question, and which part of the picture it fills.
- What is true. The evidence, cited as `path:line` or a link. Keep what the evidence shows apart from what you infer.
- What it means for the picture. Ask whether it matches what the user thought. Where it doesn't, that gap is the point of the exercise.

**Interview.**

- One question, and why you're asking it.
- Your best guess at the answer when the evidence gives you one, so the user can confirm or correct it.
- Their reply is the answer. When it changes what you still need to ask, update the list and say what changed.

### Digging

Do every dig in a subagent, however small: the survey you need to build and order the list, and each item's evidence. The main conversation reads only what the user gave you and the subagents' reports, so the reading stays out of it. Brief each subagent with the item and where to look, and ask for raw evidence cited as `path:line` or links. Inside it, `how` explains how code works and `why` finds why it was built that way. How deep to go is your call. Stop when the evidence settles the item. When it can't, because it is a judgment call or a fact only a person knows, say so and ask the user instead of guessing.

### Waiting

After each item, stop and wait. The user reads, asks follow-ups, and settles it. Move on only when they say:

- `next`: mark it done and take the next item
- `park`: set it aside with a note on what is missing, and take the next
- `skip`: drop it
- `list`: show the queue with each item's status

In Interview mode their answer moves you to the next question, so they don't need to say `next`.

## 3. Wrap up

When the queue is done, sum it up:

- Answer: each question with the answer the user settled on, or what a parked one still needs.
- Break down: the finished picture, what is still open, and where it differed from what the user first thought.
- Interview: what you learned about the user's situation, in their words where you can.

Deliver it to the output word, or ask where it should go: chat, a Markdown file, notes, an artifact, or anything else the session can make. Never commit a file this skill writes.
