from typing import Any

from app.schemas.repository import ComponentCounts


def component_counts(bom: dict[str, Any] | None) -> ComponentCounts | None:
    if not bom:
        return None
    components = bom.get("components") or []
    return ComponentCounts(
        libraries=sum(1 for c in components if c.get("type") == "library"),
        models=sum(1 for c in components if c.get("type") == "machine-learning-model"),
        services=len(bom.get("services") or []),
    )


def is_cyclonedx(document: Any) -> bool:
    return isinstance(document, dict) and document.get("bomFormat") == "CycloneDX" and isinstance(document.get("components", []), list)
