from __future__ import annotations

import sys
from collections.abc import Iterable

from .models import Diagnostic


def emit_diagnostics(diagnostics: Iterable[Diagnostic], stream=None) -> None:
    stream = stream or sys.stderr
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    for diagnostic in diagnostics:
        print(diagnostic.format(), file=stream)
