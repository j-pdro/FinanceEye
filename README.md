# FinanceEye 📊

FinanceEye é uma aplicação web desenvolvida com Streamlit para visualizar dados históricos e informações básicas de ações, utilizando dados do Yahoo Finance.



## Funcionalidades

*   Busca de dados históricos de ações (OHLCV - Open, High, Low, Close, Volume).
*   Visualização interativa do histórico de preços usando gráficos de Linha, Área ou Candlestick (Velas).
*   Exibição do nome da empresa associado ao ticker.
*   Cálculo e exibição de retornos percentuais para períodos definidos (30, 90, 365 dias).
*   Interface amigável construída com Streamlit.
*   Suporte inicial para ativos da B3 (Brasil) e NYSE/NASDAQ (EUA) com ajuste automático de sufixo (`.SA`).

## Aviso Importante sobre Fonte de Dados e Deploy

Este aplicativo utiliza a biblioteca `yfinance` para obter dados do Yahoo Finance. É importante notar que `yfinance` não é uma API oficial e depende de scraping de dados públicos do Yahoo Finance, o que pode levar a instabilidades e bloqueios por limite de taxa (Rate Limiting), especialmente em ambientes de nuvem compartilhados.

**Tentativa de Deploy:** Foi realizada uma tentativa de deploy desta aplicação no Streamlit Community Cloud. No entanto, a aplicação encontrou erros frequentes de limite de taxa (HTTP 429 "Too Many Requests") da API do Yahoo Finance. Mesmo com a implementação de mecanismos de retentativa com espera exponencial (`backoff`) no arquivo `data_fetcher.py`, os limites impostos pelo provedor de dados no ambiente de nuvem compartilhado se mostraram muito restritivos para um funcionamento estável.

**Uso Local:** Recomenda-se executar esta aplicação **localmente** em sua própria máquina. Ao rodar localmente, as requisições são feitas a partir do seu próprio endereço IP, o que **reduz significativamente** a probabilidade de encontrar os limites de taxa agressivos observados no ambiente de nuvem. No entanto, o `yfinance` ainda pode ocasionalmente falhar dependendo dos limites do Yahoo Finance.

**Adaptação para Outras APIs:** O módulo `data_fetcher.py` foi estruturado para encapsular a lógica de busca de dados. Se você possui uma chave de API para um provedor de dados financeiros diferente (como Alpha Vantage, Financial Modeling Prep, IEX Cloud, etc.), você pode adaptar as funções dentro de `data_fetcher.py` (`get_company_info`, `get_data_cached`, etc.) para utilizar essa API. Isso exigirá modificar o código para fazer as chamadas à API escolhida, tratar a autenticação (geralmente via chave de API) e ajustar o processamento para o formato de dados retornado pela nova API.

## Instalação e Execução Local

Para executar o FinanceEye em sua máquina local, siga os passos abaixo:

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/seu-usuario/financeeye.git
    cd financeeye
    ```
    *(Substitua `seu-usuario/financeeye` pelo caminho real do seu repositório)*

2.  **Crie um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    # No macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a Aplicação Streamlit:**
    ```bash
    streamlit run app.py
    ```

5.  Abra seu navegador e acesse o endereço fornecido pelo Streamlit (geralmente `http://localhost:8501`).

## Estrutura do Projeto
```text
financeeye/
│
├── .gitignore
├── app.py             # Lógica principal da aplicação Streamlit (UI)
├── data_fetcher.py    # Módulo para buscar dados da API/fonte externa
├── visualizer.py      # Módulo para gerar as visualizações (gráficos)
├── requirements.txt   # Lista de dependências Python
├── LICENSE            # Arquivo de licença (MIT)
└── README.md          # Este arquivo ```


## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir *issues* ou *pull requests*.
