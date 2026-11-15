"""Shared guards for the semantic cache backends."""

from collections.abc import Mapping
from itertools import chain
from typing import Final

_TOOL_CALL_SCAN_MAX_DEPTH: Final = 8


def _mapping_has_tool_calls(item: Mapping[str, object]) -> bool:
    tool_calls: Final = item.get("tool_calls")
    if isinstance(tool_calls, (list, tuple)) and len(tool_calls) > 0:
        return True
    return item.get("type") == "function_call"


def _child_values(value: object) -> tuple[object, ...]:
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def cached_response_has_tool_calls(response: object) -> bool:
    """Whether a decoded cached response carries a tool call.

    A semantic hit is approximate, so a cached chat completion with
    ``tool_calls`` (or a Responses API ``function_call`` output item) must
    never be served to a merely similar request. Its arguments hold exact
    per-request values, such as entity IDs, that dense embeddings blur
    together, so serving it leaks one request's arguments into another.
    """
    frontier: tuple[object, ...] = (response,)  # rebind-ok: depth-bounded frontier walk
    for _ in range(_TOOL_CALL_SCAN_MAX_DEPTH):
        if any(isinstance(item, Mapping) and _mapping_has_tool_calls(item) for item in frontier):
            return True
        frontier = tuple(chain.from_iterable(_child_values(item) for item in frontier))
        if not frontier:
            return False
    return False
