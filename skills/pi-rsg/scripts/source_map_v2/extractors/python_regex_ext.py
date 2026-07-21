"""M3 — Python extractor (regex based; zero external dependencies).

Parses Python source into per-declaration units:
  - Functions (def) → role=callable, kind=py_function
  - Classes (class) → role=class, kind=py_class
  - HTTP route decorators (@app.get, @router.post…) → role=endpoint
  - Pydantic schemas (BaseModel/RootModel subclasses) → role=schema
  - Django models (Model subclasses when framework=django) → role=model
  - Celery tasks (@task, @shared_task) → role=job

Regex-based deliberately (no tree-sitter dependency), matching the
SQL/COBOL pattern. Framework detection is passed in via ``framework`` param.
"""

from __future__ import annotations

import re
from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, get_extractor, Extractor

# ── Register kinds (role + tier) ────────────────────────────────────────
for _kind, _role, _tier in [
    ("py_function", "callable", "middle"),
    ("py_class", "class", "middle"),
    ("fastapi_endpoint", "endpoint", "middle"),
    ("flask_route", "endpoint", "middle"),
    ("http_endpoint", "endpoint", "middle"),
    ("pydantic_schema", "schema", "middle"),
    ("django_model", "model", "middle"),
    ("celery_task", "job", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)

# ── Regex patterns ─────────────────────────────────────────────────────

# Function: def name(…):
_RE_FUNC = re.compile(r"^(?P<indent>\s*)(?:async\s+)?def\s+(?P<name>[A-Za-z_]\w*)\s*\(", re.MULTILINE)

# Class: class Name(…):
_RE_CLASS = re.compile(
    r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_]\w*)(?:\s*\((?P<bases>[^)]*)\))?\s*:",
    re.MULTILINE,
)

# Decorator line: @something(… or @something
_RE_DECORATOR = re.compile(r"^(\s*)@(?P<name>[A-Za-z_]\w*)(?:\.(?P<attr>[A-Za-z_]\w*))?\s*(?:\(.*\))?", re.MULTILINE)

# HTTP route decorators: @app.get("/path"), @router.post("/path"), etc.
_RE_ROUTE_DECORATOR = re.compile(
    r"^(\s*)@(?:\w+)\.(?P<method>get|post|put|patch|delete|head|options|route|websocket)\s*\("
    r"[\"'](?P<path>[^\"']*?)[\"']",
    re.MULTILINE | re.IGNORECASE,
)

# Celery: @task(), @shared_task
_RE_CELERY = re.compile(r"@(?P<name>task|shared_task)\s*(?:\(|$)", re.MULTILINE)

# Pydantic base detection: class Foo(BaseModel): or class Foo(MealieModel):
# We collect all classes whose bases contain BaseModel/RootModel, then
# iteratively add subclasses of those.

_PYDANTIC_BASE_RE = re.compile(
    r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<bases>[^)]*)\)\s*:",
    re.MULTILINE,
)

# Django model: class Foo(models.Model): or class Foo(BaseModel): when framework=django
_DJANGO_MODEL_RE = re.compile(
    r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<bases>[^)]*)\)\s*:",
    re.MULTILINE,
)


def _collect_pydantic_bases(source: str) -> set[str]:
    """Find all Pydantic model names via fixed-point over BaseModel/RootModel inheritance."""
    pyd: set[str] = {"BaseModel", "RootModel"}
    classes: list[tuple[str, str]] = []

    for m in _PYDANTIC_BASE_RE.finditer(source):
        name = m.group("name")
        bases_raw = m.group("bases")
        # Extract simple base names (last segment after dot)
        bases = [b.strip().split(".")[-1].strip() for b in bases_raw.split(",") if b.strip()]
        classes.append((name, bases))
        if any(b in pyd for b in bases):
            pyd.add(name)

    # Fixed-point: if a class inherits from a known Pydantic base, it's Pydantic too.
    changed = True
    while changed:
        changed = False
        for name, bases in classes:
            if name not in pyd and any(b in pyd for b in bases):
                pyd.add(name)
                changed = True

    pyd.discard("BaseModel")
    pyd.discard("RootModel")
    return pyd


def _parse_bases(bases_str: str) -> list[str]:
    """Parse comma-separated base class names, extracting last segment after dot."""
    return [b.strip().split(".")[-1].strip() for b in bases_str.split(",") if b.strip()]


def _is_pydantic(bases: list[str], pydantic_bases: set[str]) -> bool:
    return any(b in {"BaseModel", "RootModel"} or b in pydantic_bases for b in bases)


def _is_django_model(bases: list[str], framework: str | None) -> bool:
    if framework != "django":
        return False
    # Check for models.Model, django.db.models.Model, or bare Model
    return any(b in {"Model", "models.Model"} for b in bases)


def _endpoint_kind(framework: str | None, method: str) -> str:
    """Name the endpoint kind by detected framework."""
    if framework == "fastapi":
        return "fastapi_endpoint"
    if framework == "flask":
        return "flask_route"
    return "http_endpoint"


def _line_at(source: str, pos: int) -> int:
    """1-based line number for a character position."""
    return source.count("\n", 0, pos) + 1


def _estimate_end_line(source: str, start_pos: int, base_indent: int) -> int:
    """Estimate the last line of a function/class body by indentation.

    Walks forward from ``start_pos`` and returns the last line whose indent
    is strictly greater than ``base_indent``.  Handles empty bodies (``...``,
    ``pass``) and single-line defs.
    """
    lines = source.split("\n")
    start_line_idx = source[:start_pos].count("\n")  # 0-based
    n = len(lines)

    last = start_line_idx  # at minimum, the declaration line itself

    for i in range(start_line_idx + 1, n):
        line = lines[i]
        if not line.strip():
            continue  # skip blank lines
        # Compute indent (spaces/tabs at start)
        stripped = line.lstrip()
        if not stripped:
            continue
        indent = len(line) - len(stripped)
        if indent > base_indent:
            last = i
        else:
            break  # dedented — body ended

    return last + 1  # convert to 1-based


class PythonRegexExtractor(Extractor):
    """Regex-based Python extractor — no tree-sitter required."""

    language = "python"

    def extract(
        self,
        path: str,
        source: str,
        id_factory: Callable[[], str],
        framework: str | None = None,
        context: dict | None = None,
    ) -> list[SourceUnit]:
        out: list[SourceUnit] = []

        # Pre-compute Pydantic inheritance graph (cross-file would need prescan,
        # but single-file is still useful).
        pydantic_bases = _collect_pydantic_bases(source)

        # ── Pass 1: collect all decorators and their associated functions/classes
        # We need to associate decorators with the next def/class.
        decorator_stack: list[tuple[int, str]] = []  # (line, full_decorator_text)

        for m in _RE_DECORATOR.finditer(source):
            decorator_stack.append((m.start(), m.group(0).strip()))

        # ── Pass 2: process functions
        for m in _RE_FUNC.finditer(source):
            name = m.group("name")
            # Find the actual position of 'def' keyword (skip leading whitespace)
            def_pos = m.start() + len(m.group("indent"))
            start_line = _line_at(source, def_pos)
            # Compute indent from the actual line content
            line_start = source.rfind("\n", 0, def_pos) + 1
            indent = def_pos - line_start
            end_line = _estimate_end_line(source, def_pos, indent)

            # Check if this function has route decorators
            routes = self._find_routes_for(name, source, m.start())

            if routes:
                method, path = routes[0]  # Take first route
                kind = _endpoint_kind(framework, method)
                sig = f"{method.upper()} {path} -> {name}"
                out.append(SourceUnit(
                    id=id_factory(), path=path, line_range=(start_line, end_line),
                    language="python", role="endpoint", kind=kind, tier="middle",
                    name=name, framework=framework, signature=sig,
                    endpoint={"method": method.upper(), "path": path},
                    fingerprint=fingerprint(sig),
                ))
            elif self._has_celery_decorator(name, source, m.start(), decorator_stack):
                sig = f"@task -> {name}"
                out.append(SourceUnit(
                    id=id_factory(), path=path, line_range=(start_line, end_line),
                    language="python", role="job", kind="celery_task", tier="middle",
                    name=name, framework=framework, signature=sig,
                    fingerprint=fingerprint(sig),
                ))
            else:
                sig = f"def {name}(...)"
                out.append(SourceUnit(
                    id=id_factory(), path=path, line_range=(start_line, end_line),
                    language="python", role="callable", kind="py_function", tier="middle",
                    name=name, framework=framework, signature=sig,
                    fingerprint=fingerprint(sig),
                ))

        # ── Pass 3: process classes
        for m in _RE_CLASS.finditer(source):
            name = m.group("name")
            bases_str = m.group("bases") or ""
            # Find the actual position of 'class' keyword (skip leading whitespace)
            class_pos = m.start() + len(m.group("indent"))
            start_line = _line_at(source, class_pos)
            # Compute indent from the actual line content
            line_start = source.rfind("\n", 0, class_pos) + 1
            indent = class_pos - line_start
            end_line = _estimate_end_line(source, class_pos, indent)
            bases = _parse_bases(bases_str)

            if _is_pydantic(bases, pydantic_bases):
                kind = "pydantic_schema"
                role = "schema"
            elif _is_django_model(bases, framework):
                kind = "django_model"
                role = "model"
            else:
                kind = "py_class"
                role = "class"

            sig = f"class {name}({bases_str})" if bases_str else f"class {name}"
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(start_line, end_line),
                language="python", role=role, kind=kind, tier="middle",
                name=name, framework=framework, signature=sig[:200],
                fingerprint=fingerprint(sig),
            ))

        # Sort by line number for deterministic output.
        out.sort(key=lambda u: u.line_range[0])
        return out

    def _find_routes_for(self, func_name: str, source: str, func_pos: int) -> list[tuple[str, str]]:
        """Find HTTP route decorators associated with a function.

        Looks for @app.get("/path"), @router.post("/path") etc. in the
        decorator block immediately preceding this function definition.
        """
        routes: list[tuple[str, str]] = []

        # Search backwards from the function for decorator lines
        prefix = source[:func_pos]
        lines_before = prefix.split("\n")

        # Walk backwards from the line before this function,
        # skipping blank lines (PEP 8 allows one blank line between
        # decorator block and function def).
        for i in range(len(lines_before) - 1, max(-1, len(lines_before) - 20), -1):
            line = lines_before[i].strip()

            # Skip blank lines (decorator block may be separated by 1 blank line)
            if not line:
                continue

            # Stop if we hit a non-decorator, non-comment line
            if not line.startswith("@") and not line.startswith("#"):
                break

            # Check for route decorator pattern
            for rm in _RE_ROUTE_DECORATOR.finditer(line):
                method = rm.group("method").lower()
                path = rm.group("path")
                routes.append((method, path))

        return routes

    def _has_celery_decorator(
        self, func_name: str, source: str, func_pos: int, decorator_stack: list[tuple[int, str]]
    ) -> bool:
        """Check if a function has @task or @shared_task decorator."""
        for dec_line, dec_text in decorator_stack:
            if dec_line >= func_pos:
                break  # decorators after this function
            # Check if this decorator is in the block immediately before the function
            dec_line_num = source.count("\n", 0, dec_line) + 1
            func_line_num = _line_at(source, func_pos)
            if func_line_num - dec_line_num <= 5:  # within 5 lines before
                if _RE_CELERY.search(dec_text):
                    return True
        return False


# ── Conditional registration (skip if tree-sitter already registered) ──
# The autoload order is: python_regex_ext first, then python_ext.
# If tree-sitter is available, python_ext overwrites; otherwise regex stays.
if get_extractor("python") is None:
    register(PythonRegexExtractor())
