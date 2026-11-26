# Recorder

`templates/record.py` holds the helpers on a `Demo` object; you write one function per beat and list them in `SCENES`, keyed by the beat id in `narration.json`. Run it with `PYTHONPATH=<skill>/scripts` so it can import `webdemo`, and with the installed Python (`~/.cache/web-demo/.venv/bin/python`), which has Playwright. The browser's viewport is the layout's app size (1600x900 for `strip`).

## Timing

- A beat lasts at least as long as its voice clip plus `beat_gap`. If the scene's clicks take longer, the voice ends early and the screen keeps moving; if they take less, the screen holds.
- `demo.speak()` marks where the beat's voice starts. Call it after the scene's page has loaded, so the voice does not talk over a blank screen. Without a call, the voice starts with the scene.
- `demo.at(seconds)` waits until that moment of the voice, counted from `speak()`. Use it to land a highlight on the word that names it: estimate the word's time from its place in the sentence and the clip's length, then adjust after looking at frames.
- `timeline.json` records where each voice starts in the video; `build.py` places the audio and captions there.

## Helpers

- `demo.move_to(locator)` glides a visible cursor there, timed by the clock (a glide counted in steps runs long, because each mouse move takes time of its own).
- `demo.click(locator)` glides, clicks with a ripple, and waits for the app to settle. `demo.click(locator, glide=0.38, settle=0.2)` for a quick repeated action.
- `demo.type(locator, text)` clicks and types at a readable speed.
- `demo.highlight(locator, seconds)` draws a frame in `style.highlight` and dims the rest for that long.
- `demo.nav(url)` loads a page fully. Single-page apps often keep state (breadcrumbs, filters, a debug mode) across a hash change; a full load gives each scene a clean start.
- `demo.settle()` waits for the app's busy indicator to go. Set `BUSY_SELECTORS` to what your app shows while it loads.
- `demo.title_card()` shows `title.html` filled from `demo.json` for the whole beat. Leave the title beat out of `narration.json` if `title_card` is false.

## Logging in

Log in outside the recording and pass the saved storage state: `record.py state.json`. Warm up the screens the take opens in that same step (open each once), so the first load in the video is not the slow one.

## Finding selectors

Before writing scenes, open each screen in a throwaway Playwright script, take a screenshot, and list the elements you will touch. Use the app's own stable names (form field names, data attributes, button names) over text and position. If the project has page objects for its end-to-end tests, take their selectors.

## When a scripted click does nothing

Some buttons ignore Playwright's clicks (a framework handler, a tooltip in the way). Check whether a request goes out when you click. If none does and a mouse click at the button's centre does nothing either, do not fight it: cut to the result with `demo.nav()` and point at what ties it to the previous screen (a source document, a reference field). Say in your message that the scene cuts there.
