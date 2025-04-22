[FinanceEye 📊](https://financeeye.streamlit.app/)


Um aplicativo web simples construído com Streamlit para visualizar dados históricos de ações e calcular retornos, utilizando dados do Yahoo Finance.

<!-- Opcional: Adicionar um screenshot ou GIF aqui depois -->
<!-- ![FinanceEye Screenshot](link_para_screenshot.png) -->

## ✨ Funcionalidades Principais

*   Busca de dados históricos de preços (OHLCV - Open, High, Low, Close, Volume) para ações.
*   Suporte para ativos da B3 (Brasil) e NYSE/NASDAQ (EUA), com ajuste automático do sufixo `.SA`.
*   Seleção de intervalo de datas customizável.
*   Visualização interativa do histórico de preços usando gráficos de Linha, Área ou Candlestick (Velas).
*   Exibição do nome completo da empresa junto ao ticker.
*   Cálculo e exibição de retornos percentuais para janelas de 30, 90 e 365 dias.
*   Interface amigável e responsiva construída com Streamlit.
*   Cache de dados para otimizar o desempenho e reduzir chamadas à API.

## 🛠️ Tecnologias Utilizadas

*   **Python:** Linguagem de programação principal.
*   **Streamlit:** Framework para criação rápida de aplicativos web de dados.
*   **yfinance:** Biblioteca para buscar dados financeiros do Yahoo Finance.
*   **Plotly:** Biblioteca para criação de gráficos interativos.
*   **Pandas:** Biblioteca para manipulação e análise de dados.

## 🚀 Instalação e Configuração

Siga os passos abaixo para configurar e executar o FinanceEye localmente:

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DA_PASTA_DO_PROJETO>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    # Para Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *Observação:* Para instalar também as ferramentas de desenvolvimento (como `pytest`, `black`), use `pip install -r requirements-dev.txt`.

## ▶️ Como Executar

Com o ambiente virtual ativado e as dependências instaladas, execute o seguinte comando no terminal, na raiz do projeto:

```bash
streamlit run app.py
