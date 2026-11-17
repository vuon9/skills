# <app> demo. Every name on screen is made up (see setup.py).
# A "#> caption" line starts a subtitle: it covers the key lines after it, up to
# the next caption, and the keys it shows are read from those lines.
Output takes/demo-01.mp4

Set Shell "bash"
Set FontSize 22
Set LineHeight 1.0
Set FontFamily "JetBrains Mono"
Set Width 1920
Set Height 940
Set Padding 24
Set TypingSpeed 70ms
Set PlaybackSpeed 0.8
Set Theme "Catppuccin Mocha"

# Hidden setup, the same for every tape: log the keys with their times, start the
# marker that flips at each subtitle, and run the app inside tmux. Change only
# the file name, demo, to the tape's own name.
Hide
Type "script -q -f --log-in $DEMO_ENV/run/demo.keys --log-timing $DEMO_ENV/run/demo.timing -c 'bash --norc'"
Enter
Sleep 1s
#! keylog
Type "source /vhs/env.sh && (python3 /opt/terminal-demo/marker.py /vhs/demo.tape $DEMO_ENV/run/demo.keys &) && tmux -u -f /opt/terminal-demo/tmux.conf new -s demo"
Enter
Sleep 2s
Type "clear"
Enter
Sleep 1s
Show

#> open the app
Type "acme"
Sleep 400ms
Enter
Sleep 3s
#> a key and what it does
Type "j"
Sleep 2s
#> quit
Type "q"
Sleep 1s
