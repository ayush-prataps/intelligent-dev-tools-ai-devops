"""Sourcegraph GraphQL integration for repository-aware retrieval.

The service is optional and fails safely when Sourcegraph is not configured.
Set SOURCEGRAPH_URL (default: http://host.docker.internal:7080) and
SOURCEGRAPH_TOKEN to enable it. Search results are returned as grounded
file/line snippets; the caller must preserve the documented uncertainty.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


DEFAULT_SOURCEGRAPH_URL = "http://host.docker.internal:7080"


async def search_sourcegraph(query: str, max_results: int = 6) -> Dict[str, Any]:
    token = os.getenv("SOURCEGRAPH_TOKEN")
    base_url = os.getenv("SOURCEGRAPH_URL", DEFAULT_SOURCEGRAPH_URL).rstrip("/")
    if not token:
        return {
            "available": False,
            "matches": [],
            "uncertainty": "Sourcegraph is not configured. Set SOURCEGRAPH_TOKEN and SOURCEGRAPH_URL; no Sourcegraph evidence was used.",
            "confidence": "low",
            "search_mode": "sourcegraph-unconfigured",
        }

    graphql = """
    query Search($query: String!, $limit: Int!) {
      search(query: $query, version: V3, patternType: standard) {
        results {
          __typename
          ... on FileMatch {
            repository { name }
            file { path }
            lineMatches { lineNumber preview }
          }
        }
      }
    }
    """
    search_query = query if "repo:" in query else f"{query} count:{max_results}"
    endpoint = f"{base_url}/.api/graphql"
    headers = {"Authorization": f"token {token}"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                endpoint,
                json={"query": graphql, "variables": {"query": search_query, "limit": max_results}},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "available": False,
            "matches": [],
            "uncertainty": f"Sourcegraph request failed: {exc}. No Sourcegraph evidence was used.",
            "confidence": "low",
            "search_mode": "sourcegraph-error",
        }

    if payload.get("errors"):
        return {
            "available": False,
            "matches": [],
            "uncertainty": "Sourcegraph returned an API error; verify the token, indexed repository and query syntax.",
            "confidence": "low",
            "search_mode": "sourcegraph-error",
            "errors": payload["errors"],
        }

    matches: List[Dict[str, Any]] = []
    for result in payload.get("data", {}).get("search", {}).get("results", []):
        if result.get("__typename") != "FileMatch":
            continue
        repository = (result.get("repository") or {}).get("name", "")
        path = result.get("file", {}).get("path", "")
        for line in (result.get("lineMatches") or []):
            line_number = int(line.get("lineNumber", 0))
            matches.append({
                "path": f"{repository}/{path}" if repository else path,
                "line_start": line_number,
                "line_end": line_number,
                "snippet": line.get("preview", ""),
                "matched_terms": [],
                "score": 1.0,
            })
            if len(matches) >= max_results:
                break
        if len(matches) >= max_results:
            break

    return {
        "available": True,
        "matches": matches,
        "uncertainty": "Sourcegraph uses search-based code navigation; results should be checked for dynamic dispatch and cross-service relationships.",
        "confidence": "medium" if matches else "low",
        "search_mode": "sourcegraph-graphql",
    }
