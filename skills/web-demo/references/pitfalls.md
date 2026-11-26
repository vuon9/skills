# Pitfalls

Each of these cost at least one take.

- **The demo showed the cases the builder liked, not the ones the audience meets.** Ask round 1 and 2 of `questions.md` and get the storyboard approved before the first take.
- **The avatar covered the data.** An overlay in a corner sits on whatever column ends up there. Put the app on top of a 1920x1080 canvas and the captions and avatar in a strip under it (`build.py` does).
- **The voice talked over a loading page.** Start each beat's voice with `demo.speak()` after the page loads, not when the scene starts.
- **The voice described a result before it appeared.** Run the slow steps first, then call `demo.speak()` over the result. A sentence like "the job created the lots" must play over the lots.
- **Long silence while typing.** A step that fills several fields can run three times longer than its sentence. Split it into beats (one per field or group) and make repeated clicks quicker.
- **Cursor glides drifted.** Moving the mouse a fixed number of steps with a sleep between each ran long and pushed every later action. Time glides by the clock.
- **State leaked between scenes.** A single-page app kept breadcrumbs and a debug mode from the previous screen. Load each scene fully (`demo.nav()`), and turn off any mode a settings screen switched on.
- **The settings screen showed the demo's plumbing.** A search for a prefix also listed the mock's own parameter, a large JSON blob. Search for exactly the settings you mean to show.
- **A re-run did nothing.** Many apps skip work on a record that already has a follow-up (a review, a lock). Show the next record instead of resetting one by hand, and say "the next one" in the narration.
- **A take changed the data.** Every take after the first failed or showed the wrong state until the data was reset. Reset before every take, even after a failure.
- **The narration promised something the app does differently.** Dry-run each scene's outcome in code against the seeded data before writing its sentence, and read the app's own messages: they are often better narration than yours.
- **Frames were checked at one moment per beat.** A beat can be right at its end and wrong at its start. `frames.py` takes two frames per beat.
- **A label with `%` broke ffmpeg's drawtext.** Keep labels to letters, numbers and spaces.
