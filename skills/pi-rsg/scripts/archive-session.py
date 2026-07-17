#!/usr/bin/env python3
"""
pi-rsg archive-session.py

Упаковывает артефакты текущей сессии pi-rsg в отдельный каталог
`analysis/<session-name>/`, затем очищает `rds/` для новой сессии.

Использование:
    python archive-session.py [--session-name <name>] [--dry-run]

Если --session-name не указан, генерируется автоматически:
    <project-name>-<YYYYMMDD>-<HHMMSS>

Аргументы:
    --session-name   Имя сессии (по умолчанию auto-generated)
    --dry-run        Показать что будет сделано, но не выполнять
    --target-dir     Путь к rds (по умолчанию rds в текущем каталоге)
    --output-dir     Путь для архива (по умолчанию analysis/ в текущем каталоге)

Что сохраняется:
    - Все JSON-файлы (rds/*.json): goal.json, state.json, inventory.json,
      wbs.json, questions.json, source-map.json, trace.json, coverage-report.json
    - Все MD-файлы (rds/*.md): recon-report.md, coverage-report.md
    - Каталог drafts/ (все черновики глав)
    - Каталог final/ (финальная спецификация)

Что удаляется после архивации:
    - drafts/* (черновики — они уже в final/)
    - state.json, questions.json (состояние сессии)
    - coverage-report.json/md (отчёт проверки — тоже в архиве)

Что сохраняется в rds/ после очистки:
    - goal.json (цели сессии — могут понадобиться для новой сессии)
    - recon-report.md (рекон — справочная информация)
    - inventory.json, wbs.json (инвентарь и WBS — справочная информация)
    - source-map.json (карта исходников — может понадобиться)

Примеры:
    # Автоматическое имя сессии
    python archive-session.py

    # Явное имя сессии
    python archive-session.py --session-name my-project-v1

    # Только показать что будет сделано
    python archive-session.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive pi-rsg session artifacts and clean rds/"
    )
    parser.add_argument(
        "--session-name",
        type=str,
        default=None,
        help="Session name (default: auto-generated from project + timestamp)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default="rds",
        help="Path to rds directory (default: rds)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="rds/archive",
        help="Output directory for archives (default: rds/archive)",
    )
    return parser.parse_args()


def generate_session_name(target_dir: str) -> str:
    """Generate a session name from project directory + timestamp."""
    project_dir = Path.cwd()
    project_name = project_dir.name

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")

    return f"{project_name}-{timestamp}"


def get_session_info(target_dir: str) -> dict | None:
    """Extract session metadata from goal.json if available."""
    goal_path = Path(target_dir) / "goal.json"
    if not goal_path.exists():
        return None

    try:
        with open(goal_path, "r", encoding="utf-8") as f:
            goal = json.load(f)

        return {
            "primary_reader": goal.get("primary_reader", "unknown"),
            "depth_mode": goal.get("depth_mode", "unknown"),
            "output_language": goal.get("output_language", "ru"),
        }
    except (json.JSONDecodeError, KeyError):
        return None


def list_artifacts(target_dir: str) -> dict[str, list[str]]:
    """List all artifacts that will be archived."""
    target = Path(target_dir)

    artifacts: dict[str, list[str]] = {
        "json_files": [],
        "md_files": [],
        "drafts": [],
        "final": [],
    }

    # JSON files in rds/
    for f in sorted(target.glob("*.json")):
        if f.is_file():
            artifacts["json_files"].append(f.name)

    # MD files in rds/
    for f in sorted(target.glob("*.md")):
        if f.is_file():
            artifacts["md_files"].append(f.name)

    # drafts/ directory
    drafts_dir = target / "drafts"
    if drafts_dir.exists() and drafts_dir.is_dir():
        for f in sorted(drafts_dir.glob("*.md")):
            if f.is_file():
                artifacts["drafts"].append(f.name)

    # final/ directory
    final_dir = target / "final"
    if final_dir.exists() and final_dir.is_dir():
        for f in sorted(final_dir.glob("*.md")):
            if f.is_file():
                artifacts["final"].append(f.name)

    return artifacts


def archive_session(
    target_dir: str,
    output_dir: str,
    session_name: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Archive session artifacts and clean rds.

    Returns a dict with counts: {archived, cleaned, kept}
    """
    target = Path(target_dir)
    output = Path(output_dir)

    if not target.exists():
        print(f"ERROR: {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Create session directory
    session_dir = output / session_name
    if not dry_run:
        session_dir.mkdir(parents=True, exist_ok=True)

    counts = {"archived": 0, "cleaned": 0, "kept": 0}

    # --- Archive JSON files ---
    json_dest = session_dir / "json"
    if not dry_run:
        json_dest.mkdir(exist_ok=True)

    for fname in target.glob("*.json"):
        if fname.is_file():
            dest = json_dest / fname.name
            if not dry_run:
                shutil.copy2(fname, dest)
            counts["archived"] += 1

    # --- Archive MD files (recon, coverage report) ---
    md_dest = session_dir / "reports"
    if not dry_run:
        md_dest.mkdir(exist_ok=True)

    for fname in target.glob("*.md"):
        if fname.is_file():
            dest = md_dest / fname.name
            if not dry_run:
                shutil.copy2(fname, dest)
            counts["archived"] += 1

    # --- Archive drafts/ ---
    drafts_src = target / "drafts"
    if drafts_src.exists():
        drafts_dest = session_dir / "drafts"
        if not dry_run:
            shutil.copytree(drafts_src, drafts_dest)
        counts["archived"] += len(list_artifacts(target_dir)["drafts"])

    # --- Archive final/ ---
    final_src = target / "final"
    if final_src.exists():
        final_dest = session_dir / "final"
        if not dry_run:
            shutil.copytree(final_src, final_dest)
        counts["archived"] += len(list_artifacts(target_dir)["final"])

    # --- Write session metadata ---
    if not dry_run:
        info = get_session_info(target_dir)
        metadata = {
            "session_name": session_name,
            "archived_at": datetime.now().isoformat(),
            "source_dir": str(target.resolve()),
        }
        if info:
            metadata["session_info"] = info

        with open(session_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    # --- Clean rds/ (remove drafts, state, questions, coverage reports) ---
    files_to_clean = [
        "state.json",
        "questions.json",
        "coverage-report.json",
        "coverage-report.md",
    ]

    for fname in files_to_clean:
        fpath = target / fname
        if fpath.exists():
            if not dry_run:
                fpath.unlink()
            counts["cleaned"] += 1

    # Clean drafts/ directory (but keep the dir itself)
    if drafts_src.exists():
        for f in drafts_src.glob("*.md"):
            if f.is_file():
                if not dry_run:
                    f.unlink()
                counts["cleaned"] += 1

    # Clean final/ directory (files are already archived)
    final_src = target / "final"
    if final_src.exists():
        for f in final_src.glob("*.md"):
            if f.is_file():
                if not dry_run:
                    f.unlink()
                counts["cleaned"] += 1

    # Clean stale subdirectories that may remain from previous runs:
    # - scripts/ (copied by agent during run, not needed after)
    # - skill/ (marker directory from old staging procedure)
    # NOTE: do NOT remove transformed/ — it's output from pi-rsg-transform
    stale_dirs = ["scripts", "skill"]
    for dirname in stale_dirs:
        dpath = target / dirname
        if dpath.exists() and dpath.is_dir():
            # Only remove if empty or contains only session artifacts
            children = list(dpath.iterdir())
            if not children:
                # Empty directory — remove it
                if not dry_run:
                    dpath.rmdir()
                counts["cleaned"] += 1
            else:
                # Check if all children are .md files (session artifacts)
                md_only = all(c.is_file() and c.suffix == ".md" for c in children)
                if md_only:
                    # Remove all files, then the directory
                    for c in children:
                        if not dry_run:
                            c.unlink()
                        counts["cleaned"] += 1
                    if not dry_run:
                        dpath.rmdir()
                    counts["cleaned"] += 1
                # If directory contains non-.md files (e.g. scripts/), leave it alone

    # --- Keep these files in rds/ for reference ---
    kept_files = [
        "goal.json",
        "recon-report.md",
        "inventory.json",
        "wbs.json",
        "source-map.json",
    ]

    for fname in kept_files:
        fpath = target / fname
        if fpath.exists():
            counts["kept"] += 1

    return counts


def main() -> None:
    args = parse_args()

    target_dir = args.target_dir
    output_dir = args.output_dir

    # Generate session name if not provided
    if args.session_name:
        session_name = args.session_name
    else:
        session_name = generate_session_name(target_dir)

    print(f"pi-rsg archive-session")
    print(f"{'=' * 50}")
    print(f"Target directory: {target_dir}/")
    print(f"Output directory: {output_dir}/")
    print(f"Session name:     {session_name}")

    # List current artifacts
    artifacts = list_artifacts(target_dir)
    total_files = (
        len(artifacts["json_files"])
        + len(artifacts["md_files"])
        + len(artifacts["drafts"])
        + len(artifacts["final"])
    )

    print(f"\nCurrent artifacts ({total_files} files):")
    if artifacts["json_files"]:
        print(f"  JSON: {', '.join(artifacts['json_files'])}")
    if artifacts["md_files"]:
        print(f"  Reports: {', '.join(artifacts['md_files'])}")
    if artifacts["drafts"]:
        print(f"  Drafts: {len(artifacts['drafts'])} files")
    if artifacts["final"]:
        print(f"  Final: {len(artifacts['final'])} files")

    if args.dry_run:
        print(f"\n[DRY RUN] Would archive to: {output_dir}/{session_name}/")
        print(f"Would clean: state.json, questions.json, coverage-report.*, drafts/*")
        print(f"Would keep in rds/: goal.json, recon-report.md, inventory.json, wbs.json, source-map.json")
        return

    # Archive
    counts = archive_session(target_dir, output_dir, session_name)

    print(f"\nDone!")
    print(f"  Archived: {counts['archived']} files → {output_dir}/{session_name}/")
    print(f"  Cleaned:  {counts['cleaned']} files from rds/")
    print(f"  Kept:     {counts['kept']} files in rds/ (reference)")
    print(f"\nSession archived at: {output_dir}/{session_name}/")


if __name__ == "__main__":
    main()
