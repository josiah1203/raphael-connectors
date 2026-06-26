"""KiCad S-expression file parser (Phase 1a file-parse)."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _parse_sexpr(text: str) -> Any:
    """Parse KiCad S-expression text into nested lists."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\n\r":
            i += 1
            continue
        if c == "(":
            tokens.append("(")
            i += 1
        elif c == ")":
            tokens.append(")")
            i += 1
        elif c == '"':
            i += 1
            start = i
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    i += 2
                else:
                    i += 1
            tokens.append(text[start:i])
            i += 1
        else:
            start = i
            while i < n and text[i] not in " \t\n\r()":
                i += 1
            tokens.append(text[start:i])

    def parse_list(idx: int = 0) -> tuple[Any, int]:
        items: list[Any] = []
        i = idx
        while i < len(tokens):
            tok = tokens[i]
            if tok == "(":
                sub, i = parse_list(i + 1)
                items.append(sub)
            elif tok == ")":
                return items, i + 1
            else:
                items.append(tok)
                i += 1
        return items, i

    if tokens and tokens[0] == "(":
        result, _ = parse_list(1)
        return result
    return tokens


def parse_kicad_pcb(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8-sig") as f:
        content = f.read()
    if not content.strip().endswith(")"):
        raise ValueError("partial_write")
    tree = _parse_sexpr(content)
    footprints: list[dict[str, Any]] = []
    nets: list[str] = []

    def walk(node: Any):
        if not isinstance(node, list) or not node:
            return
        tag = node[0] if isinstance(node[0], str) else None
        if tag == "footprint":
            ref = ""
            for child in node[1:]:
                if isinstance(child, list) and child:
                    if child[0] == "property" and len(child) > 2 and child[1] == "Reference":
                        ref = str(child[2])
                    elif child[0] == "fp_text" and len(child) > 2 and child[1] == "reference":
                        ref = str(child[2])
            footprints.append({"reference": ref or f"fp-{len(footprints)}", "raw_len": len(str(node))})
        elif tag == "net":
            if len(node) > 2:
                nets.append(str(node[2]))
        for child in node[1:]:
            walk(child)

    walk(tree)
    return {
        "filename": path,
        "footprints": footprints,
        "nets": sorted(set(nets)),
        "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
    }


def diff_kicad_snapshots(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if previous is None:
        for fp in current.get("footprints", []):
            changes.append({"type": "electrical.footprint_added", "footprint_ref": fp.get("reference", "")})
        for net in current.get("nets", []):
            changes.append({"type": "electrical.net_changed", "net_name": net, "change": "baseline"})
        return changes

    prev_fps = {f.get("reference"): f for f in previous.get("footprints", [])}
    curr_fps = {f.get("reference"): f for f in current.get("footprints", [])}
    for ref, fp in curr_fps.items():
        if ref not in prev_fps:
            changes.append({"type": "electrical.footprint_added", "footprint_ref": ref})
        elif prev_fps[ref] != fp:
            changes.append({"type": "electrical.footprint_modified", "footprint_ref": ref})

    prev_nets = set(previous.get("nets", []))
    curr_nets = set(current.get("nets", []))
    for net in curr_nets - prev_nets:
        changes.append({"type": "electrical.net_changed", "net_name": net, "change": "added"})
    for net in prev_nets - curr_nets:
        changes.append({"type": "electrical.net_changed", "net_name": net, "change": "removed"})

    return changes
