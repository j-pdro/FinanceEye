# app.py
"""
FinanceEye – aplicativo Streamlit para visualização de preços
"""

from datetime import date, timedelta
from typing import List
import logging
import time # <--- ALTERAÇÃO: Importar time

import pandas as pd
import streamlit as st

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from data_fetcher import get_data_cached, get_company_info
from visualizer import plot_price_history

# Aumentado para tentar garantir dados para retorno de 365 dias
DEFAULT_LOOKBACK_DAYS = 550
RETURNS_WINDOWS: List[int] = [30, 90, 365]
# Formato CORRETO para st.date_input
DATE_FORMAT = "DD/MM/YYYY"
# Opções de mercado com bandeiras
MARKET_OPTIONS = ["🇧🇷 Brasil (B3)", "🇺🇸 EUA (NYSE/NASDAQ)"]

def adjust_ticker(ticker: str, market: str) -> str:
    """Ajusta o sufixo do ticker com base no mercado selecionado."""
    ticker = ticker.strip().upper()
    if market == MARKET_OPTIONS[0]: # Brasil
        if not ticker.endswith(".SA"):
            logger.info(f"Adicionando sufixo '.SA' ao ticker {ticker}")
            return f"{ticker}.SA"
    elif market == MARKET_OPTIONS[1]: # EUA
        if ticker.endswith(".SA"):
            logger.info(f"Removendo sufixo '.SA' do ticker {ticker}")
            return ticker[:-3]
    return ticker

def main() -> None:
    st.set_page_config(page_title="FinanceEye", layout="wide")
    st.title("📊 FinanceEye")

    with st.sidebar:
        st.header("Configurações")
        with st.form(key="input_form"):
            market = st.radio(
                "Selecione o Mercado",
                options=MARKET_OPTIONS,
                index=0,
                horizontal=True,
            )
            raw_ticker = st.text_input(
                "Código do ativo",
                placeholder="Ex: PETR4 ou AAPL"
            )
            end_dt = st.date_input(
                "Data final",
                value=date.today(),
                format=DATE_FORMAT
            )
            start_dt = st.date_input(
                "Data inicial",
                value=end_dt - timedelta(days=DEFAULT_LOOKBACK_DAYS),
                max_value=end_dt - timedelta(days=1),
                format=DATE_FORMAT
            )
            chart_type = st.selectbox(
                "Tipo de gráfico",
                ["line", "area", "candlestick"],
                index=0,
                format_func=lambda x: {"line": "Linha", "area": "Área", "candlestick": "Velas"}[x],
            )
            submitted = st.form_submit_button("📈 Buscar")

    if submitted:
        if not raw_ticker:
            st.error("Informe um código de ativo.")
            st.stop()

        if start_dt >= end_dt:
            st.error("A data inicial deve ser anterior à data final.")
            st.stop()

        ticker = adjust_ticker(raw_ticker, market)
        st.info(f"Buscando dados para o ticker ajustado: {ticker}")

        company_name = ticker # Fallback inicial
        df = pd.DataFrame() # Inicializa df como vazio

        try:
            with st.spinner(f"Carregando dados para {ticker}..."):
                # 1. Busca informações da empresa (nome, etc.)
                # A função get_company_info já tem retentativas e retorna fallback em caso de erro
                company_info = get_company_info(ticker)
                company_name = company_info.get("longName", ticker)

                # <--- ALTERAÇÃO: Adiciona uma pequena pausa antes da próxima chamada de API --->
                time.sleep(0.5)
                # <---------------------------------------------------------------------------->

                # 2. Busca dados históricos
                # A função get_data_cached já tem retentativas e levanta ValueError em caso de erro
                df = get_data_cached(ticker, start=start_dt, end=end_dt)

        except ValueError as err:
            # <--- ALTERAÇÃO: Mensagem de erro mais informativa --->
            st.error(f"Erro ao buscar dados para {ticker}: {err}")
            st.warning(
                "Falhas podem ocorrer devido a limites da API gratuita do provedor de dados. "
                "Por favor, tente novamente em alguns instantes ou verifique o código do ativo."
            )
            # Sugestões baseadas no mercado (mantidas)
            if market == MARKET_OPTIONS[0] and ".SA" not in ticker:
                 st.warning("Verifique se o código do ativo da B3 está correto (ex: PETR4) e se a opção '🇧🇷 Brasil (B3)' está selecionada.")
            elif market == MARKET_OPTIONS[1] and ".SA" in ticker:
                 st.warning("Verifique se o código do ativo dos EUA está correto (ex: AAPL) e se a opção '🇺🇸 EUA (NYSE/NASDAQ)' está selecionada.")
            st.stop() # Para a execução
            # <----------------------------------------------------->
        except Exception as e: # Captura outros erros inesperados
            st.error(f"Ocorreu um erro inesperado durante o processamento.")
            logger.exception(f"Erro inesperado ao processar {ticker}: {e}") # Loga o traceback completo
            st.stop() # Para a execução

        # ----- Exibição dos Resultados -----
        # A verificação df.empty não é mais necessária aqui, pois ValueError seria levantado antes
        # if df.empty: ... (removido anteriormente)

        st.subheader(f"Visualização para {company_name} ({ticker})")

        # ----- Gráfico -----
        try:
            fig = plot_price_history(
                df,
                ticker=ticker,
                company_name=company_name,
                chart_type=chart_type
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error("Ocorreu um erro ao gerar o gráfico.")
            logger.exception(f"Erro ao gerar gráfico para {ticker}: {e}")
            st.stop()


        # ----- Retornos -----
        st.subheader("Retornos percentuais no período")
        metrics = []
        # Verifica se df não está vazio antes de calcular retornos
        if not df.empty:
            for days in RETURNS_WINDOWS:
                if len(df) > days and -days-1 < len(df.index):
                     try:
                         current_price = df["Close"].iloc[-1]
                         past_price = df["Close"].iloc[-days-1]
                         if pd.notna(current_price) and pd.notna(past_price) and past_price != 0:
                             pct = (current_price / past_price - 1) * 100
                             metrics.append((f"{days} dias", f"{pct:,.2f}%"))
                         else:
                              metrics.append((f"{days} dias", "N/D"))
                     except IndexError:
                         logger.warning(f"IndexError ao calcular retorno de {days} dias para {ticker}. len(df)={len(df)}")
                         metrics.append((f"{days} dias", "N/D"))
                else:
                    metrics.append((f"{days} dias", "N/D"))

            if metrics:
                cols = st.columns(len(metrics))
                for i, (label, value) in enumerate(metrics):
                    cols[i].metric(label, value)
            else:
                st.info("Não foi possível calcular retornos para as janelas padrão.")
        else:
             # Isso não deve acontecer devido ao tratamento de erro anterior, mas por segurança:
             st.warning("Não foi possível calcular retornos pois os dados históricos não foram carregados.")


    else:
        st.info("Configure os parâmetros na barra lateral e clique em 'Buscar' ou pressione Enter no campo do ativo.")


if __name__ == "__main__":
    main()