from __future__ import annotations

from typing import Callable

from workflow.pipeline import Pipeline


WorkflowFactory = Callable[[], Pipeline]
_WORKFLOW_REGISTRY: dict[str, WorkflowFactory] = {}


def register_workflow(name: str, factory: WorkflowFactory, *, overwrite: bool = False) -> None:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Workflow name cannot be empty.")
    if clean_name in _WORKFLOW_REGISTRY and not overwrite:
        raise KeyError(f"Workflow already registered: {clean_name}")
    _WORKFLOW_REGISTRY[clean_name] = factory


def get_workflow(name: str) -> Pipeline:
    clean_name = name.strip()
    if clean_name not in _WORKFLOW_REGISTRY:
        raise KeyError(f"Workflow is not registered: {clean_name}")
    return _WORKFLOW_REGISTRY[clean_name]()


def list_workflows() -> list[str]:
    return sorted(_WORKFLOW_REGISTRY)


def clear_workflows() -> None:
    _WORKFLOW_REGISTRY.clear()

