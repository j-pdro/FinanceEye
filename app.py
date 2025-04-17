import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="FinanceEye", layout="wide")

# --- Função para buscar e limpar os dados ---
@st.cache_data
def fetch_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

# --- Título e descrição ---
st.title("📊 FinanceEye")
st.markdown(
    "Visualize e compare ações das bolsas **B3 🇧🇷** ou **EUA 🇺🇸** com dados históricos interativos."
)

# --- Seleção da bolsa ---
market = st.radio(
    "Escolha a bolsa de valores:",
    ["🇧🇷 Brasil (B3)", "🇺🇸 EUA (NASDAQ/NYSE)"]
)
suffix = ".SA" if "Brasil" in market else ""

# --- Entrada do ticker ---
ticker_input = st.text_input(
    "Digite o código do ativo (ex: PETR4, AAPL)",
    value=""
).strip().upper()

# --- Datas padrão ---
end_date = date.today()
start_date = end_date - timedelta(days=400)

# --- Botão para buscar dados ---
if st.button("📈 Buscar dados") and ticker_input:
    ticker = ticker_input + suffix
    df = fetch_data(ticker, start_date, end_date)

    if df.empty:
        st.warning(
            "⚠️ Nenhum dado encontrado para esse ativo. Verifique o código e a bolsa selecionada."
        )
    else:
        st.success(f"✅ Dados carregados para: {ticker}")

        # Exibir dados brutos em expander
        with st.expander("📄 Visualizar dados brutos"):
            st.dataframe(df.tail(10))

        # --- Seleção da coluna de preço ---
        preco_coluna = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
        if preco_coluna not in df.columns:
            st.error(
                "❌ Coluna de preço ajustado ('Adj Close') ou fechamento ('Close') não encontrada."
            )
        else:
            # --- Gráfico interativo ---
            st.subheader(f"📈 Gráfico de preços - {ticker}")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[preco_coluna],
                    mode='lines',
                    name='Preço'
                )
            )
            fig.update_layout(
                title=f"Evolução do preço de {ticker}",
                xaxis_title="Data",
                yaxis_title="Preço (R$ ou US$)",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Tabela de retorno percentual ---
            st.subheader("📊 Retorno percentual")
            retorno_30 = ((df[preco_coluna].iloc[-1] / df[preco_coluna].iloc[-30]) - 1) * 100 if df.shape[0] >= 30 else None
            retorno_90 = ((df[preco_coluna].iloc[-1] / df[preco_coluna].iloc[-90]) - 1) * 100 if df.shape[0] >= 90 else None
            retorno_365 = ((df[preco_coluna].iloc[-1] / df[preco_coluna].iloc[-365]) - 1) * 100 if df.shape[0] >= 365 else None

            tabela_retornos = pd.DataFrame(
                {
                    "Retorno (%)": [
                        f"{retorno_30:.2f}%" if retorno_30 is not None else "N/D",
                        f"{retorno_90:.2f}%" if retorno_90 is not None else "N/D",
                        f"{retorno_365:.2f}%" if retorno_365 is not None else "N/D",
                    ]
                },
                index=["30 dias", "90 dias", "1 ano"],
            )
            tabela_retornos.index.name = "Período"
            st.table(tabela_retornos)
