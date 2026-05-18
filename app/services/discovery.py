"""Auto-discovery of *arr service credentials from their config.xml files."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

_ARR_SERVICES: dict[str, tuple[str, int]] = {
    "radarr": ("radarr", 7878),
    "sonarr": ("sonarr", 8989),
    "lidarr": ("lidarr", 8686),
}


@dataclass
class ServiceDiscovery:
    status: str          # "discovered" | "not_found" | "parse_error"
    url: str = ""
    api_key: str = ""


def discover_service(name: str) -> ServiceDiscovery:
    hostname, default_port = _ARR_SERVICES[name]
    path = Path(f"/arr/{name}/config.xml")

    if not path.exists():
        return ServiceDiscovery(status="not_found")

    try:
        root = ET.parse(path).getroot()
        api_key = (root.findtext("ApiKey") or "").strip()
        port_text = (root.findtext("Port") or "").strip()
        port = int(port_text) if port_text.isdigit() else default_port
        if not api_key:
            return ServiceDiscovery(status="parse_error")
        return ServiceDiscovery(
            status="discovered",
            url=f"http://{hostname}:{port}",
            api_key=api_key,
        )
    except Exception:
        return ServiceDiscovery(status="parse_error")


def discover_all() -> dict[str, ServiceDiscovery]:
    return {name: discover_service(name) for name in _ARR_SERVICES}
