# fix: retry unavailable watcher backends instead of exiting

On GNOME Wayland without the Focused Window D-Bus extension, active-window
backend discovery exhausts its candidates and returns `false`. `main` selects
completion of either watcher task, so this also terminates otherwise working
idle tracking. In the desktop bundle it exits with status 0 and is not restarted.

Keep the affected task alive and retry backend discovery every 30 seconds.
A working idle watcher can continue reporting while the window extension is
unavailable, and discovery can recover when the extension becomes available.
Log an actionable GNOME extension hint when no window backend was found.

Validation: release build with cached dependencies (`cargo build --release --offline`).
The Rust test suite could not run offline because a dev dependency was not cached.
This change handles initial discovery failures; errors from an already selected
backend retain the existing retry behavior.
