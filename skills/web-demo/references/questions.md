# Align before building

A demo misses when it answers a question nobody in the room asked. Before writing a scene, ask the human these, in rounds, and record the answers in `demo.json` (choices in their keys, everything else under `notes`). Use the harness's question tool when it has one: up to four questions a round, the recommended option first and marked, one sentence of why under each option. Fill in what the code, the tickets or the conversation already settle, and say what you assumed instead of asking it.

Before round 2, look at the feature yourself (code, tests, tickets, existing manual test cases) so the case options are real, named, and counted where you can count them.

## Round 1: audience and purpose

1. **Who will watch?** Operations or business leads (default for a feature walkthrough) / executives / engineers / customers or end users. Sets wording and how much of the screen you explain. Notes: `audience`.
2. **What should they do after watching?** Approve a rollout / try it themselves on a test system / understand what changes in their daily work / give feedback on the flow. Sets the last scene and its closing line. Notes: `goal`.
3. **What do you think they most want to see?** Proof that it works end to end / the exceptions and who handles them / numbers on the impact / what changes in their day / the settings and how the rollout stays safe. Usually more than one; it decides which scenes get time. Notes: `wants`.
4. **How deep?**
   - *Overview*, 1 to 2 minutes: the happy path and its result.
   - *Standard* (recommended for stakeholders), 3 to 5 minutes: the data first, the happy path, the two or three exceptions they will meet, the settings.
   - *Deep*, 6 to 10 minutes or a short series: every case, including failures and edge cases.

   Notes: `depth`, `length`.

## Round 2: content

1. **Which cases?** List the cases you found, with how often each happens if you can tell, and let the human pick (several allowed). Mark the ones the audience meets most. Notes: `cases`.
2. **Show the data first?** Yes (recommended): what comes in, where it lives, the queue people work from, then what the feature does with it / No: straight to the feature. Notes: `data_first`.
3. **Numbers on screen?** Only figures with a source the human can name (a replay, a report). Ask for the source; leave numbers out otherwise. Notes: `numbers`.
4. **What must not appear?** Real customer or staff names, prices, internal URLs, unreleased features, anything under NDA. Seed data to avoid them. Notes: `avoid`.

## Round 3: format and style

1. **Layout** (`layout`):
   - `strip` (recommended): 16:9, the app on top and captions with the avatar in a band under it. Nothing covers the app.
   - `full`: 16:9, the app fills the frame and captions sit on a band over its bottom edge. Bigger app, but the band can hide the bottom rows.
   - `portrait`: 9:16, a phone-sized app with a tall band, for vertical players and phones.
2. **Look:** brand colours for the frame and accent (`style.background`, `style.accent`), the highlight colour (`style.highlight`), a title card with title, subtitle and a small footer such as "Sample data" (`title_card`, `title`, `subtitle`, `title_footer`).
3. **The narrator on screen:** the bot avatar and its name (`avatar.show`, `avatar.name`), or none.
4. **Captions:** burned in (`captions`), a separate `.srt` for players that show their own (`captions_file`), or both (recommended).

## Round 4: voice

1. **Which voice?** (`voice.engine`)
   - `kokoro` (recommended): free and offline. Render a sentence from the script in a few voices with `scripts/voice_samples.py`, send the files, and let the human pick by ear (`voice.id`).
   - `recorded`: the human reads the timed script, one WAV per beat named `out/<beat>.wav`. Most natural; costs their time and a quiet room.
   - A hosted voice (ElevenLabs, OpenAI and others): better than Kokoro, but the script goes to that vendor. Only with the human's explicit yes; generate one WAV per beat and use `recorded`.
   - `none`: captions only. Beats last as long as it takes to read them; hide the avatar.
2. **Pace:** speed 0.9 (calmer), 1.0 (recommended), 1.1 (brisk) (`voice.speed`).
3. **Tone and language:** plain business words or technical terms; "we" or neutral; the language. Notes: `tone`, `language`.

## Round 5: environment and honesty

1. **Where to record?** A local copy with seeded data (recommended: repeatable, no real data) / a shared test system (needs access and a way to reset) / production, read only (avoid: real data on screen). Notes: `environment`.
2. **What is faked, and how is it disclosed?** List every mock (an external API, a payment provider). Disclose on the title card footer, in the narration, or only in your message to the human. Notes: `disclose`.
3. **Off-camera steps:** may a scene cut past a slow job or a manual fix, if the narration says so? Notes: `off_camera`.

## Round 6: review and delivery

1. **Review points:** the storyboard (scenes and narration) before any recording (recommended), then one scene as a proof clip, then the full take. Notes: `review`.
2. **Delivery:** MP4, plus `.srt`; a size limit; where it will be posted and who can see it. Notes: `delivery`.

## After the rounds

Write the storyboard: one line per scene with what is on screen and its narration, in the order you will record it. Get a yes on it before step 5 of the pipeline. If an answer changes later (a new case, a different audience), update `demo.json` and the storyboard before recording again.
