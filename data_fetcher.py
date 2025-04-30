# data_fetcher.py
from __future__ import annotations

from datetime import date
import logging
import time 
from typing import Literal, Optional, Dict, Any

import pandas as pd
import yfinance as yf

try:
    import streamlit as st
except ModuleNotFoundError:
    import functools

    # Mock para permitir execução/teste fora do Streamlit
    def st_cache_mock(func=None, **_kwargs):
        return functools.lru_cache(maxsize=32)(func)

    class _StMock: # type: ignore
        cache_data = st_cache_mock
        cache_resource = st_cache_mock

    st = _StMock() # type: ignore

#
logger = logging.getLogger(__name__)
# ---------------------------

Period = Literal[
    "1d", "5d", "1mo", "3mo", "6mo", "1y",
    "2y", "5y", "10y", "ytd", "max",
]

# Função auxiliar para retry 
def fetch_with_retry(api_call_func, max_retries=5, initial_delay=2):
    """Tenta executar uma função de chamada de API com retentativas e backoff."""
    retries = 0
    delay = initial_delay
    while retries < max_retries:
        try:
            result = api_call_func()
            return result # Sucesso!
        except Exception as e:
            error_str = str(e).lower()
            # Verifica erros que justificam retentativa (429, JSON, talvez conexão)
            if "429" in error_str or "too many requests" in error_str or \
               "expecting value" in error_str or "jsondecodeerror" in error_str or \
               "failed to get ticker" in error_str or "no timezone found" in error_str:

                retries += 1
                if retries >= max_retries:
                    
                    logger.error(f"Máximo de retentativas ({max_retries}) atingido para API call. Erro final: {e}")
                    raise e # Levanta a última exceção após esgotar retentativas

               
                logger.warning(f"API call falhou (tentativa {retries}/{max_retries}): {e}. Tentando novamente em {delay}s...")
                time.sleep(delay)
                delay *= 2 # Backoff exponencial
            else:
                # Se for outro tipo de erro, não tenta novamente e levanta imediatamente
                
                logger.error(f"Erro não recuperável na API call: {e}")
                raise e
    # Caso o loop termine sem sucesso 
    raise Exception("Falha na chamada da API após múltiplas tentativas.")



def _download(
    ticker: str,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period: Optional[Period] = "6mo",
) -> pd.DataFrame:
    """Wrapper sobre yfinance.download com retentativas."""
    # Usa logger aqui (agora definido)
    logger.info(f"Tentando baixar dados para {ticker} com yf.download (com retries)...")

    def api_call(): # Encapsula a chamada em uma função para passar para fetch_with_retry
        if start is not None:
            return yf.download(ticker, start=start, end=end, progress=False)
        else:
            return yf.download(ticker, period=period, progress=False)

    try:
        # Usa a função auxiliar de retry
        df = fetch_with_retry(api_call)
    except Exception as e:
        # Se fetch_with_retry falhar após todas as tentativas, levanta ValueError
        # Usa logger aqui (agora definido)
        logger.error(f"Falha final ao baixar dados para {ticker} após retentativas: {e}")
        raise ValueError(f"Falha ao tentar baixar dados para '{ticker}' após múltiplas tentativas. Causa: {e}")

    if df.empty:
        # Usa logger aqui (agora definido)
        logger.warning(f"yf.download retornou DataFrame vazio para '{ticker}' no período solicitado. Ticker pode ser inválido, delistado, sem dados no período ou houve um problema na API.")
        raise ValueError(f"Nenhum dado encontrado para '{ticker}' no período solicitado (ou ticker inválido/delistado).")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.sort_index(inplace=True)
    return df


@st.cache_data(ttl=86400, show_spinner=False)
def get_company_info(ticker: str) -> Dict[str, Any]:
    """Busca informações da empresa com retentativas."""
    # Usa logger aqui 
    logger.info(f"Buscando informações da empresa para {ticker} (com retries)...")

    try:
        tkr = _get_ticker_obj(ticker)

        def api_call(): # Encapsula a chamada .info
            return tkr.info

        # Usa a função auxiliar de retry
        info = fetch_with_retry(api_call)

        # Verificações e fallback como antes...
        if not info or not isinstance(info, dict) or 'symbol' not in info:
             # Usa logger aqui (agora definido)
             logger.warning(f"Informações básicas ('info') não encontradas ou inválidas para {ticker} após retries.")
             return {"longName": info.get("shortName", ticker)} if isinstance(info, dict) else {"longName": ticker}
        if "longName" not in info or not info["longName"]:
             info["longName"] = info.get("shortName", ticker)
        return info

    except Exception as e:
        # Se fetch_with_retry falhar após todas as tentativas
        # Usa logger aqui (agora definido)
        logger.error(f"Falha final ao buscar info para {ticker} após retentativas: {e}")
        # Retorna fallback para não quebrar o app
        return {"longName": ticker}


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
    return _download(ticker, start=start, end=end, period=period)


@st.cache_resource(ttl=86400, show_spinner=False) # Cache de 1 dia para o objeto
def _get_ticker_obj(ticker: str) -> yf.Ticker:
    """Retorna um objeto yfinance.Ticker em cache."""
    # Usa logger aqui (agora definido)
    logger.info(f"Criando ou recuperando objeto Ticker em cache para {ticker}...")
    return yf.Ticker(ticker)

