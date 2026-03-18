import sys

# Enable UTF-8 output on Windows so Rich can render Unicode block art (U+2588 etc.)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console

from powerglide.cli.main import app

try:
    app()
except KeyboardInterrupt:
    Console().print("\n[dim]Interrupted. Exiting PowerGlide.[/dim]")
    sys.exit(0)
