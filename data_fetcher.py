# data_fetcher.py
from __future__ import annotations

from datetime import date
import logging
from typing import Literal, Optional, Dict, Any

import pandas as pd
import yfinance as yf

try:
    import streamlit as st
except ModuleNotFoundError:
    import functools

    def st_cache_mock(func=None, **_kwargs):
        return functools.lru_cache(maxsize=32)(func)

    class _StMock: # type: ignore
        cache_data = st_cache_mock
        cache_resource = st_cache_mock # Mock para cache_resource também

    st = _StMock() # type: ignore


logger = logging.getLogger(__name__)

Period = Literal[
    "1d", "5d", "1mo", "3mo", "6mo", "1y",
    "2y", "5y", "10y", "ytd", "max",
]


def _download(
    ticker: str,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period: Optional[Period] = "6mo",
) -> pd.DataFrame:
    """Wrapper fino sobre `yfinance.download`."""
    # yfinance pode retornar dados mesmo com ticker inválido às vezes,
    # então validamos com Ticker primeiro
    tkr = yf.Ticker(ticker)
    if not tkr.history(period="1d").empty: # Checa se o ticker existe/tem dados
        if start is not None:
            df = yf.download(ticker, start=start, end=end, progress=False)
        else:
            df = yf.download(ticker, period=period, progress=False)
    else:
        raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados históricos.")


    if df.empty:
        raise ValueError(f"Nenhum dado encontrado para '{ticker}' no período solicitado.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.sort_index(inplace=True)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_data_cached(
    ticker: str,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period: Optional[Period] = "6mo",
) -> pd.DataFrame:
    """Versão em cache (1h) para buscar dados históricos."""
    logger.info(f"Buscando dados históricos para {ticker}...")
    return _download(ticker, start=start, end=end, period=period)


# Usamos cache_resource para o objeto Ticker, pois ele é mais pesado
@st.cache_resource(ttl=86400, show_spinner=False) # Cache de 1 dia
def _get_ticker_obj(ticker: str) -> yf.Ticker:
    """Retorna um objeto yfinance.Ticker em cache."""
    logger.info(f"Criando objeto Ticker para {ticker}...")
    return yf.Ticker(ticker)


@st.cache_data(ttl=86400, show_spinner=False) # Cache de 1 dia
def get_company_info(ticker: str) -> Dict[str, Any]:
    """Busca informações básicas da empresa (nome, setor, etc.)."""
    logger.info(f"Buscando informações da empresa para {ticker}...")
    try:
        tkr = _get_ticker_obj(ticker)
        info = tkr.info
        if not info or 'symbol' not in info: # Checa se info veio vazia ou inválida
             logger.warning(f"Informações básicas não encontradas para {ticker}.")
             return {"longName": ticker} # Retorna o próprio ticker como fallback
        return info
    except Exception as e:
        logger.error(f"Erro ao buscar info para {ticker}: {e}")
        return {"longName": ticker} # Fallback em caso de erro na API