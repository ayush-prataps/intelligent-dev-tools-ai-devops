"""Lightweight repository search used by the Week 5 codebase assistant.

This intentionally avoids a complex agent or external dependency. It searches the
application repository available inside the runtime, returns line-addressable
snippets, and exposes uncertainty when the query has weak evidence.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

_ALLOWED_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".md", ".json",
    ".yml", ".yaml", ".toml", ".txt", ".sh",
}
_EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".mypy_cache",
}


def _repository_roots() -> List[Path]:
    configured = os.getenv("REPOSITORY_ROOT")
    candidates = [
        Path(configured) if configured else None,
        Path("/app"),
        Path(__file__).resolve().parents[3],
        Path.cwd(),
    ]
    roots: List[Path] = []
    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_dir() and candidate not in roots:
            roots.append(candidate)
    return roots


def _files() -> List[Path]:
    seen = set()
    result: List[Path] = []
    for root in _repository_roots():
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
                continue
            if any(part in _EXCLUDED_DIRS for part in path.parts):
                continue
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                result.append(path)
    return result


def _tokens(value: str) -> List[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_/-]+", value) if len(token) > 1]


def _relative_path(path: Path) -> str:
    for root in _repository_roots():
        try:
            return str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            continue
    return str(path)


def search_repository(query: str, max_results: int = 6) -> Dict[str, Any]:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return {
            "query": query,
            "matches": [],
            "uncertainty": "The query did not contain searchable terms.",
            "confidence": "low",
        }

    ranked = []
    for path in _files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            line_tokens = set(_tokens(line))
            overlap = query_tokens.intersection(line_tokens)
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            start = max(0, index - 2)
            end = min(len(lines), index + 3)
            ranked.append({
                "path": _relative_path(path),
                "line_start": start + 1,
                "line_end": end,
                "snippet": "\n".join(lines[start:end]),
                "matched_terms": sorted(overlap),
                "score": round(score, 4),
            })

    ranked.sort(key=lambda item: (-item["score"], item["path"], item["line_start"]))
    unique = []
    seen = set()
    for item in ranked:
        key = (item["path"], item["line_start"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= max(1, min(max_results, 20)):
            break

    if not unique:
        uncertainty = "No matching source snippets were found. The assistant should not claim repository-level evidence."
        confidence = "low"
    elif unique[0]["score"] < 0.5:
        uncertainty = "Matches are partial; verify the snippets before treating the answer as conclusive."
        confidence = "medium"
    else:
        uncertainty = "Results are based on lexical source matching, not a complete semantic or Sourcegraph index."
        confidence = "medium"

    return {
        "query": query,
        "matches": unique,
        "uncertainty": uncertainty,
        "confidence": confidence,
        "search_mode": "local-lexical",
    }
