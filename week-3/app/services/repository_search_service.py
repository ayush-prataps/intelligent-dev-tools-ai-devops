from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

_ALLOWED_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".sh"}
_EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build", ".mypy_cache", ".idea", ".vscode"}


def _repository_roots() -> List[Path]:
    configured = os.getenv("REPOSITORY_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        return [root] if root.is_dir() else []
    module = Path(__file__).resolve()
    roots = [module.parents[3], module.parents[2], Path.cwd()]
    return list(dict.fromkeys(root for root in roots if root.is_dir()))[:2]


def _files() -> List[Path]:
    result, seen = [], set()
    for root in _repository_roots():
        try:
            for path in root.rglob("*"):
                if len(result) >= 5000:
                    return result
                if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
                    continue
                if any(part in _EXCLUDED_DIRS for part in path.parts):
                    continue
                resolved = str(path.resolve())
                if resolved not in seen:
                    seen.add(resolved)
                    result.append(path)
        except OSError:
            continue
    return result


def _tokens(value: str) -> List[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_/-]+", value or "") if len(token) > 1]


def _relative_path(path: Path) -> str:
    for root in _repository_roots():
        try:
            return str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            pass
    return str(path)


def search_repository(query: str, max_results: int = 6) -> Dict[str, Any]:
    query = query or ""
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return {"query": query, "matches": [], "uncertainty": "The query did not contain searchable terms.", "confidence": "low", "search_mode": "local-lexical"}

    ranked = []
    for path in _files():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            overlap = query_tokens.intersection(set(_tokens(line)))
            if not overlap:
                continue
            start, end = max(0, index - 2), min(len(lines), index + 3)
            ranked.append({"path": _relative_path(path), "line_start": start + 1, "line_end": end, "snippet": "\n".join(lines[start:end]), "matched_terms": sorted(overlap), "score": round(len(overlap) / max(len(query_tokens), 1), 4)})

    ranked.sort(key=lambda item: (-item["score"], item["path"], item["line_start"]))
    unique, seen = [], set()
    for item in ranked:
        key = (item["path"], item["line_start"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= max(1, min(max_results, 20)):
            break

    if not unique:
        uncertainty, confidence = "No matching source snippets were found. The assistant should not claim repository-level evidence.", "low"
    elif unique[0]["score"] < 0.5:
        uncertainty, confidence = "Matches are partial; verify the snippets before treating the answer as conclusive.", "medium"
    else:
        uncertainty, confidence = "Results are based on lexical source matching, not a complete semantic or Sourcegraph index.", "medium"
    return {"query": query, "matches": unique, "uncertainty": uncertainty, "confidence": confidence, "search_mode": "local-lexical"}
