---
name: unslop
description: Use when writing or editing any text; cut AI tells and add human voice.
---

# Unslop

Edit text to remove AI patterns and add human voice.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Add soul (see next section).

## Adding soul

Removing patterns is half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

## Patterns to detect and fix

### Content

1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.
2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.
3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.
4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.
5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.
6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.

### Language

7. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
8. **Fancy ways to say "is".** "serves as", "stands as", "boasts", "features". Just say "is" or "has".
9. **"Not just X, but Y."** State the point directly instead.
10. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
11. **Synonym cycling.** Protagonist, main character, central figure, hero all in one paragraph. Pick one, repeat it.
12. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

13. **Em dash overuse.** Avoid em dashes entirely. Use a period or a comma. Parentheses are fine for a short definition or aside, such as the first time a term appears. No en dashes and no hyphen-as-dash substitutes. Em dashes are an AI tell. If a thought needs separation, end the sentence or use a comma.
14. **Colon overuse.** Colons are fine before a list or example. Not as mid-sentence connectors. "If you're coming from traditional automation: instead of registering event handlers, you describe conditions" adds nothing with the colon. Rewrite to let the point stand on its own without comparison framing. "Describing when the scheduler should fire works best as plain English." Same meaning, no crutch punctuation.
15. **Boldface overuse.** Don't bold every proper noun or acronym.
16. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine, not a tell.
17. **Title case headings.** Use sentence case.
18. **Decorative emojis.** Remove from headings and bullets.
19. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.
22. **Sycophantic tone.** "Great question! You're absolutely right!" Respond directly.

### Filler

23. **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
24. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
25. **Generic conclusions.** "The future looks bright." State specific plans or facts.

### Jargon

26. **Abstract metaphor nouns.** Substrate, wedge, vector, locus, vantage, nexus, primitive (as noun), harness (as metaphor), surface (as in "API surface"), bedrock, scaffolding (as metaphor), modality, paradigm, gold-plating, ratchet (as metaphor), evacuate (for moving code), endgame, north star, flywheel. These read as technical but usually have a plainer concrete word. "Substrate" becomes "base". "Wedge in" becomes "add". "Vector" becomes "way" or "method". "Gold-plating" becomes "more than the job needs". "Ratchet" becomes the mechanism's real name or "a limit that only tightens". "Evacuate" becomes "move out". "Endgame" becomes "the last phase". Pick the concrete word.

### Plain speech

27. **Say what it does, not how it feels.** "the database stays close at hand", "SQL you can read", "types that follow your schema" name a feeling. The fix names the mechanism or a number: "`.toSQL()` returns the exact string sent to the database", "a column rename fails the build". Ask what the sentence tells the reader to do or know, then write that. If you can't restate it as a concrete instruction, fact, or number, cut it. One more check: if the sentence could appear unchanged in another project's docs, it says nothing about this one. Cut it.
28. **Shorten or split dense sentences.** If the reader has to backtrack to parse a sentence, break it in two or drop clauses. One idea per sentence.
29. **Active voice.** Prefer it. Catch "is/are/was/were + past participle" and name the actor: "queries are validated" becomes "the compiler validates queries", "the file is parsed by the loader" becomes "the loader parses the file". Passive is fine only when the actor is unknown or genuinely doesn't matter.
30. **Cut adverbs, or use a stronger verb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta. An adverb propping up a weak verb means the verb is wrong.
31. **Prefer the plain word.** "utilize" becomes "use", "leverage" becomes "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if". The fancier synonym is rarely clearer.
32. **Give every number a referent, or cut it.** A figure with no noun saying what it measures, over what window, and for whom is a maintenance trap: the reader cannot check it, and nothing marks it as stale later. A count that will change as the thing grows ("eight skills") is the same trap in miniature. Keep numbers for claims that need proof, not as decoration. Scattering digits through prose ("3 of the 5 services, 2 with 14 retries") reads like a dashboard leaked into a paragraph; a sentence making no quantitative claim needs no number. Pick one form and stay with it, `3` or `three`, not both in the same text.

### Structure

Short, clean sentences can still add up to text nobody can follow. These patterns live at the paragraph level.

33. **Jargon headline.** The first line leans on a label coined during the work, such as "Pinned holds survive the shuffle" or "the staging run", before anything explains it. Open with what changed, in words the reader already uses. Explain each label before you lean on it.
34. **Discovery order.** The text follows the order the writer found things in: verdict, background, mechanism, a side case, evidence, the fix, then one more fact. Reorder for the reader. Background, then how it works, then what changed, then the evidence. When two versions differ, state what they share once, then the difference. Side cases and gaps go last, in their own short block.
35. **Numbers woven through the explanation.** Counts, dates, and IDs placed between the steps of an explanation make the reader hold figures while following the logic. A number may stay in an explanation sentence when the noun it counts sits beside it, one number per sentence. Evidence goes after the explanation in a short list, one claim per line.

Before:

> Pinned holds survive the shuffle (not in the staging run: it ends before the shuffle). Both flows set a returned book aside for the first patron waiting. A patron with an expired card gets no hold and goes to the front desk. Since April 2, the old flow gave away 6 held copies at 2 branches, and at one branch 4 patrons came in for books that were gone. The old flow only marks the copy, so the nightly shuffle hands it to the next patron. The new flow pins it, and the shuffle skips it.

After:

> **A returned book held for a patron now stays on the hold shelf overnight.**
>
> When a held book comes back, the library sets the copy aside for the patron who asked first. Every night, a job called the shuffle moves free copies to the patrons who have waited longest. The old flow only marked the copy as set aside, and the shuffle did not check that mark, so it could hand the copy to someone else. The new flow pins the copy to the patron, and the shuffle skips pinned copies.
>
> What the old flow did since April 2:
> - It gave away 6 held copies across 2 branches.
> - At one branch, 4 patrons came in for books that were already gone.
>
> Not covered:
> - A patron with an expired card gets no hold. The front desk handles it.
> - The staging run ends before the shuffle, so it does not exercise this change.
