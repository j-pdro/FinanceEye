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

# Função auxiliar para retry (pode ser colocada no início do arquivo)
def fetch_with_retry(api_call_func, max_retries=3, initial_delay=1):
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
    # Caso o loop termine sem sucesso (não deveria acontecer devido ao raise acima, mas por segurança)
    raise Exception("Falha na chamada da API após múltiplas tentativas.")


# --- Modificar _download ---
def _download(
    ticker: str,
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
    period: Optional[Period] = "6mo",
) -> pd.DataFrame:
    """Wrapper sobre yfinance.download com retentativas."""
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
        logger.error(f"Falha final ao baixar dados para {ticker} após retentativas: {e}")
        raise ValueError(f"Falha ao tentar baixar dados para '{ticker}' após múltiplas tentativas. Causa: {e}")

    if df.empty:
        logger.warning(f"yf.download retornou DataFrame vazio para '{ticker}'...") # Mensagem como antes
        raise ValueError(f"Nenhum dado encontrado para '{ticker}'...") # Mensagem como antes

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.sort_index(inplace=True)
    return df

# --- Modificar get_company_info ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_company_info(ticker: str) -> Dict[str, Any]:
    """Busca informações da empresa com retentativas."""
    logger.info(f"Buscando informações da empresa para {ticker} (com retries)...")

    try:
        tkr = _get_ticker_obj(ticker)

        def api_call(): # Encapsula a chamada .info
            return tkr.info

        # Usa a função auxiliar de retry
        info = fetch_with_retry(api_call)

        # Verificações e fallback como antes...
        if not info or not isinstance(info, dict) or 'symbol' not in info:
             logger.warning(f"Informações básicas ('info') não encontradas ou inválidas para {ticker} após retries.")
             return {"longName": info.get("shortName", ticker)} if isinstance(info, dict) else {"longName": ticker}
        if "longName" not in info or not info["longName"]:
             info["longName"] = info.get("shortName", ticker)
        return info

    except Exception as e:
        # Se fetch_with_retry falhar após todas as tentativas
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