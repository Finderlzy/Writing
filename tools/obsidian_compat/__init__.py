"""Build-time compatibility layer for Obsidian Markdown."""

from .models import ConversionResult, Diagnostic, Reference, ResolvedTarget, SourceSpan

__all__ = [
    "ConversionResult",
    "Diagnostic",
    "Reference",
    "ResolvedTarget",
    "SourceSpan",
]
