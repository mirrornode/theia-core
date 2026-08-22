from __future__ import annotations

import posixpath
import unicodedata

PROTECTED_ROOTS = (".git", ".github")
_MAX_PATH_BYTES = 1024


class PathPolicyError(ValueError):
    """A path does not provably denote a bounded resource inside the repository."""


def normalize_repo_path(path: str) -> str:
    """Return the canonical repository-relative POSIX identity or fail closed.

    The returned identity, never the caller's original spelling, is the value
    that should participate in comparisons, uniqueness checks, and digests.
    """
    if not isinstance(path, str):
        raise PathPolicyError(f"path must be a string, got {type(path).__name__}")
    if path == "":
        raise PathPolicyError("path is empty")
    if len(path.encode("utf-8")) > _MAX_PATH_BYTES:
        raise PathPolicyError("path exceeds maximum length")
    for ch in path:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            raise PathPolicyError(f"path contains control character {ord(ch):#04x}")
    if "\\" in path:
        raise PathPolicyError("path contains a backslash")
    if path.startswith("/"):
        raise PathPolicyError("path is absolute")
    if path.startswith("~"):
        raise PathPolicyError("path is home-relative")
    if len(path) >= 2 and path[1] == ":":
        raise PathPolicyError("path carries a drive letter")
    if path.endswith("/"):
        raise PathPolicyError("path has a trailing separator and denotes no file")

    normalized = unicodedata.normalize("NFC", path)
    segments = normalized.split("/")
    if any(segment == "" for segment in segments):
        raise PathPolicyError("path contains an empty segment")
    if any(segment == "." for segment in segments):
        raise PathPolicyError("path contains a '.' segment")
    if any(segment == ".." for segment in segments):
        raise PathPolicyError("path contains a '..' segment")
    if any(segment in {" ", "\t"} or segment != segment.strip() for segment in segments):
        raise PathPolicyError("path segment has leading or trailing whitespace")

    canonical = posixpath.normpath(normalized)
    if canonical != normalized:
        raise PathPolicyError(
            f"path is not canonical ({normalized!r} normalizes to {canonical!r})"
        )
    if canonical.startswith("..") or posixpath.isabs(canonical):
        raise PathPolicyError("path escapes repository root")
    return canonical


def is_within(path: str, root: str) -> bool:
    path_n = normalize_repo_path(path)
    root_n = normalize_repo_path(root)
    return path_n == root_n or path_n.startswith(root_n + "/")


def is_protected(path: str) -> bool:
    normalized = normalize_repo_path(path)
    head = normalized.split("/", 1)[0]
    return head in PROTECTED_ROOTS


def check_unique_identities(paths: list[str] | tuple[str, ...], *, label: str = "paths") -> list[str]:
    seen: dict[str, str] = {}
    canonical_paths: list[str] = []
    for raw in paths:
        canonical = normalize_repo_path(raw)
        if canonical in seen:
            raise PathPolicyError(
                f"{label}: {raw!r} and {seen[canonical]!r} denote the same resource {canonical!r}"
            )
        seen[canonical] = raw
        canonical_paths.append(canonical)
    return canonical_paths


def validate_artifact_path(path: str, artifact_root: str) -> str:
    normalized = normalize_repo_path(path)
    root = normalize_repo_path(artifact_root)
    if is_protected(root) or is_protected(normalized):
        raise PathPolicyError("verification artifacts may not target protected control roots")
    if not is_within(normalized, root):
        raise PathPolicyError("verification artifact is outside the declared positive artifact root")
    return normalized
