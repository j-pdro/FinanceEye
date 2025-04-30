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

    # Mock para permitir execução/teste fora do Streamlit
    def st_cache_mock(func=None, **_kwargs):
        # Usando lru_cache como um substituto simples para cache
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
    """
    Wrapper fino sobre `yfinance.download`, otimizado para reduzir chamadas API.
    """
    # REMOVIDA a validação extra com tkr.history(period="1d")
    # Tenta baixar os dados diretamente. yf.download lida com tickers inválidos
    # retornando um DataFrame vazio ou levantando uma exceção em alguns casos.
    logger.info(f"Tentando baixar dados para {ticker} com yf.download...")
    try:
        if start is not None:
            df = yf.download(ticker, start=start, end=end, progress=False)
        else:
            df = yf.download(ticker, period=period, progress=False)
    except Exception as e:
        # Captura exceções que podem ocorrer durante o download (ex: rede)
        logger.error(f"Erro durante yf.download para {ticker}: {e}")
        # Levanta um ValueError para ser tratado no app.py
        raise ValueError(f"Falha ao tentar baixar dados para '{ticker}'. Causa: {e}")

    # Verifica se o DataFrame está vazio APÓS a tentativa de download
    if df.empty:
        # Log específico para DataFrame vazio
        logger.warning(f"yf.download retornou DataFrame vazio para '{ticker}' no período solicitado. Ticker pode ser inválido, delistado, sem dados no período ou houve um problema na API.")
        # Levanta o ValueError que será pego no app.py
        raise ValueError(f"Nenhum dado encontrado para '{ticker}' no período solicitado (ou ticker inválido/delistado).")

    # Limpa MultiIndex se existir (comportamento padrão do yfinance para múltiplos tickers)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.sort_index(inplace=True)
    return df


@st.cache_data(ttl=3600, show_spinner=False) # Cache de 1h para dados históricos
def get_data_cached(
    ticker: str,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period: Optional[Period] = "6mo",
) -> pd.DataFrame:
    """Versão em cache para buscar dados históricos."""
    logger.info(f"Chamando _download para dados históricos de {ticker}...")
    # A exceção ValueError de _download será propagada e deve ser tratada
    # onde get_data_cached é chamada (no app.py)
    return _download(ticker, start=start, end=end, period=period)


# Usamos cache_resource para o objeto Ticker, pois ele é mais pesado e
# pode ser reutilizado para buscar diferentes tipos de info (.info, .actions, etc.)
@st.cache_resource(ttl=86400, show_spinner=False) # Cache de 1 dia para o objeto
def _get_ticker_obj(ticker: str) -> yf.Ticker:
    """Retorna um objeto yfinance.Ticker em cache."""
    logger.info(f"Criando ou recuperando objeto Ticker em cache para {ticker}...")
    return yf.Ticker(ticker)


@st.cache_data(ttl=86400, show_spinner=False) # Cache de 1 dia para os dados de info
def get_company_info(ticker: str) -> Dict[str, Any]:
    """
    Busca informações básicas da empresa (nome, setor, etc.) com tratamento
    de erro aprimorado para falhas de API e rate limiting.
    """
    logger.info(f"Buscando informações da empresa para {ticker}...")
    try:
        # Obtém o objeto Ticker (potencialmente do cache de resource)
        tkr = _get_ticker_obj(ticker)
        # Acessa a propriedade .info (que faz a chamada de API se não estiver no cache implícito do objeto)
        info = tkr.info

        # Verificação mais robusta se 'info' é válido
        # Alguns tickers (ex: fundos) podem não ter 'longName' ou outras chaves esperadas
        if not info or not isinstance(info, dict) or 'symbol' not in info:
             logger.warning(f"Informações básicas ('info') não encontradas, vazias ou em formato inesperado para {ticker}. Retornando fallback.")
             # Tenta usar shortName se longName não estiver disponível, senão usa o ticker
             return {"longName": info.get("shortName", ticker)} if isinstance(info, dict) else {"longName": ticker}

        # Se longName não existir, tenta usar shortName como fallback antes de retornar o dict
        if "longName" not in info or not info["longName"]:
             info["longName"] = info.get("shortName", ticker)

        return info

    except Exception as e:
        # Tratamento de erro mais detalhado
        error_str = str(e).lower()
        if "429" in error_str or "too many requests" in error_str:
             logger.error(f"Erro de Rate Limit (429) ao buscar info para {ticker}: {e}")
             # Retorna fallback, mas poderia levantar exceção específica se necessário
             # raise RateLimitError(f"Limite de taxa atingido ao buscar info para {ticker}")
        elif "failed to get ticker" in error_str or "expecting value" in error_str or "jsondecodeerror" in error_str:
             logger.error(f"Provável erro de API/JSON ao buscar info para {ticker}: {e}")
        else:
             # Outros erros inesperados (rede, etc.)
             logger.error(f"Erro inesperado ao buscar info para {ticker}: {e}")

        # Retorna um dicionário de fallback para não quebrar o app.py
        return {"longName": ticker}