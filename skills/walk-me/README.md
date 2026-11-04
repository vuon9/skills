# walk-me

When too much lands on you at once, `walk-me` takes it one item at a time,
with evidence for each, and waits for you between items. It handles three
kinds of work:

- **Answer.** Questions people sent you about a codebase you are still
  learning. For each one you get what the person is asking and why, where the
  answer lives, and a suggested reply to check before you send it.
- **Break down.** A problem or a black box. It turns it into questions and
  answers them one by one with evidence, until your picture matches what is
  true.
- **Interview.** It asks you questions one at a time to understand your
  situation, then writes up what it learned.

## Use it with a prompt

- `/walk-me` -> reads the recent conversation, proposes a topic, a mode and
  the items, and waits for your go
- `/walk-me <questions, a problem, a doc or links>` -> picks the mode, shows
  the order and starts on item 1 right away
- `/walk-me md ...` -> the first word picks where the result goes. `md`
  saves a Markdown file, and `html`, `artifact`, `notes` or anything else the
  session can make works too. Without one, it asks when the work is done.

During the walk-through:

- `next` -> mark the item done and move on
- `park` -> set it aside with a note on what is missing
- `skip` -> drop it
- `list` -> show the queue and each item's status

## Relationship to other skills

Each item's digging runs in a subagent, which uses `how` for how the code
works and `why` for why it was built that way. Break down questions
the problem instead of your plan. It never posts
anything. It drafts, and you send.

## TODO

- Pull new questions from connected sources (issue tracker, chat, PR reviews)
  instead of starting from what is pasted.
