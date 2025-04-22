# visualizer.py
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def plot_price_history(
    df: pd.DataFrame,
    ticker: str,
    *,
    company_name: str | None = None,
    y_column: str = "Close",
    chart_type: str = "line",  # "line" | "area" | "candlestick"
) -> go.Figure:
    """
    Gera figura Plotly com histórico de preços.

    chart_type pode ser:
      • line – linha simples
      • area – linha preenchida
      • candlestick – OHLC (requer colunas Open/High/Low/Close)
    """
    fig = go.Figure()

    if chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=ticker,
            )
        )
    else:
        fill = "tozeroy" if chart_type == "area" else None
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[y_column],
                mode="lines",
                fill=fill,
                name=ticker,
            )
        )

    title = f"Histórico de Preços – {ticker}"
    if company_name:
        title += f" — {company_name}"

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title="Preço",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig