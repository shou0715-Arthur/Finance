from __future__ import annotations

from data_sources.news_client import deduplicate_news, normalize_news_records
from research.catalyst_calendar import build_catalyst_calendar
from research.event_extractor import extract_events
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def normalize_news_step(context: WorkflowContext) -> WorkflowContext:
    records = deduplicate_news(normalize_news_records(context.data["news_rows"]))
    return context.with_value("news_records", records)


def extract_events_step(context: WorkflowContext) -> WorkflowContext:
    return context.with_value("events", extract_events(context.data["news_records"]))


def catalyst_calendar_step(context: WorkflowContext) -> WorkflowContext:
    return context.with_value("catalyst_calendar", build_catalyst_calendar(str(context.data["ticker"]), context.data["events"]))


def build_event_monitoring_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_event_inputs", ("ticker", "news_rows")),
            FunctionStep("normalize_news", normalize_news_step),
            FunctionStep("extract_events", extract_events_step),
            FunctionStep("build_catalyst_calendar", catalyst_calendar_step),
        ],
        name="event_monitoring",
    )

