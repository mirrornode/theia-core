from __future__ import annotations

import posixpath
import re

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
PROTECTED_ROOTS = (".git", ".github")


class PathPolicyError(ValueError):
    pass


def normalize_repo_path(path: str) -> str:
    """Return a canonical repository-relative POSIX path or fail closed."""
    if not isinstance(path, str) or not path:
        raise PathPolicyError("path must be a non-empty string")
    if _CONTROL.search(path):
        raise PathPolicyError("control characters are forbidden")
    if "\\" in path:
        raise PathPolicyError("backslashes are forbidden; use repository-relative POSIX paths")
    if path.startswith("/"):
        raise PathPolicyError("absolute paths are forbidden")
    if path.endswith("/"):
        raise PathPolicyError("trailing separators are forbidden")

    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PathPolicyError("empty, '.' and '..' path segments are forbidden")

    normalized = posixpath.normpath(path)
    if normalized != path:
        raise PathPolicyError("path must already be in canonical normalized form")
    if normalized == ".." or normalized.startswith("../"):
        raise PathPolicyError("path escapes repository root")
    return normalized


def is_within(path: str, root: str) -> bool:
    path_n = normalize_repo_path(path)
    root_n = normalize_repo_path(root)
    return path_n == root_n or path_n.startswith(root_n + "/")


def is_protected(path: str) -> bool:
    normalized = normalize_repo_path(path)
    return any(normalized == root or normalized.startswith(root + "/") for root in PROTECTED_ROOTS)


def validate_artifact_path(path: str, artifact_root: str) -> str:
    normalized = normalize_repo_path(path)
    root = normalize_repo_path(artifact_root)
    if is_protected(root) or is_protected(normalized):
        raise PathPolicyError("verification artifacts may not target protected control roots")
    if not is_within(normalized, root):
        raise PathPolicyError("verification artifact is outside the declared positive artifact root")
    return normalized
