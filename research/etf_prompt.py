from __future__ import annotations

from dataclasses import dataclass, field

from analytics.etf_overlap import ETFOverlapResult, Holding


@dataclass(frozen=True)
class ETFPromptContext:
    symbol: str
    holdings_count: int
    top_holdings: list[dict[str, float | str]]
    country_exposure: dict[str, float] = field(default_factory=dict)
    sector_exposure: dict[str, float] = field(default_factory=dict)
    overlap: ETFOverlapResult | None = None
    ptp_warnings: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)


def build_etf_prompt_context(
    symbol: str,
    holdings: list[Holding],
    top_holdings: list[dict[str, float | str]],
    *,
    country_exposure: dict[str, float] | None = None,
    sector_exposure: dict[str, float] | None = None,
    overlap: ETFOverlapResult | None = None,
    ptp_holdings: list[Holding] | None = None,
    missing_data: list[str] | None = None,
) -> ETFPromptContext:
    return ETFPromptContext(
        symbol=symbol.upper(),
        holdings_count=len(holdings),
        top_holdings=top_holdings,
        country_exposure=country_exposure or {},
        sector_exposure=sector_exposure or {},
        overlap=overlap,
        ptp_warnings=[holding.identifier for holding in (ptp_holdings or [])],
        missing_data=missing_data or [],
    )


def render_etf_prompt_summary(context: ETFPromptContext) -> str:
    lines = [
        f"ETF：{context.symbol}",
        f"持股數：{context.holdings_count}",
        "前大持股：",
    ]
    for holding in context.top_holdings:
        lines.append(f"- {holding['identifier']} {holding['name']} {holding['weight']:.2%}")
    if context.overlap:
        lines.append(f"重疊持股數：{context.overlap.common_count}")
        lines.append(f"重疊權重：{context.overlap.overlap_weight:.2%}")
    if context.ptp_warnings:
        lines.append("PTP 警示：" + ", ".join(context.ptp_warnings))
    if context.missing_data:
        lines.append("缺資料：" + ", ".join(context.missing_data))
    return "\n".join(lines)

