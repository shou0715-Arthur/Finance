from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SelfControlResult:
    name: str
    ok: bool
    message: str


def check_required_path(name: str, path: Path, *, should_exist: bool = True) -> SelfControlResult:
    exists = path.exists()
    if should_exist and not exists:
        return SelfControlResult(name=name, ok=False, message=f"Missing required path: {path}")
    return SelfControlResult(name=name, ok=True, message=f"OK: {path}")


def run_startup_self_controls(project_root: Path) -> list[SelfControlResult]:
    """Run non-blocking startup checks.

    These checks are intentionally conservative: they report obvious wiring
    problems without blocking the desktop app. Runtime features still perform
    their own local validation and fallback.
    """

    checks = [
        check_required_path("master_spec", project_root / "docs" / "CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md"),
        check_required_path("research_prompt", project_root / "research" / "public_equity_prompt.py"),
        check_required_path("memo_contract", project_root / "research" / "memo_contract.py"),
        check_required_path("config_dir", project_root / "config"),
    ]
    return checks
