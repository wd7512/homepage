"""Inbound/outbound port protocols (depend inward on the domain only)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from domain.models import DomainBundle


class LoaderPort(Protocol):
    """Inbound adapter: read the Markdown source into the domain bundle."""

    def load(self, content_dir: Path) -> DomainBundle: ...


class RenderPort(Protocol):
    """Outbound adapter: render a (possibly channel-filtered) bundle."""

    channel: str

    def render(self, bundle: DomainBundle) -> str: ...
