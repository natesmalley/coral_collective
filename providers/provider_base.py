#!/usr/bin/env python3
"""
Provider Base

Defines a minimal interface for rendering and delivering prompts for different providers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import pyperclip  # type: ignore
except Exception:
    pyperclip = None


class BaseProvider:
    name = "base"

    def render(self, payload) -> str:  # noqa: ANN001 - generic payload
        raise NotImplementedError

    def render_sections(self, sections) -> str:  # noqa: ANN001 - generic sections
        # Generic fallback rendering using simple headings
        lines = []
        for s in sections:
            title = s.get('title', s.get('key', 'SECTION'))
            lines.append(f"## {title}")
            lines.append(str(s.get('text', '')))
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def deliver(
        self,
        output_text: str,
        mode: str = "stdout",
        base_dir: Path = Path("prompts"),
        filename_stub: Optional[str] = None,
    ) -> Optional[Path]:
        """Deliver output via stdout, clipboard, or file. Returns path if saved."""
        if mode == "stdout":
            print(output_text)
            return None
        elif mode == "clipboard":
            if pyperclip:
                try:
                    pyperclip.copy(output_text)
                except Exception:
                    # Fallback: also print to stdout
                    print(output_text)
            else:
                # Fallback: no clipboard available
                print(output_text)
            return None
        elif mode == "file":
            base_dir.mkdir(exist_ok=True, parents=True)
            filename = (filename_stub or "prompt").replace(" ", "_") + ".md"
            path = base_dir / filename
            path.write_text(output_text)
            return path
        else:
            # Unknown mode -> stdout
            print(output_text)
            return None
