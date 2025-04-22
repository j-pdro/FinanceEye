# FinanceEye

**Propósito:** Auxiliar investidores a visualizar e entender melhor suas carteiras com gráficos interativos e dados financeiros reais.

## Funcionalidades

- Ajuste automático de tickers para mercados do Brasil (B3) e EUA (NYSE/NASDAQ).
- Busca de informações básicas da empresa, como nome e setor.
- Obtenção de dados históricos de preços com cache para otimizar desempenho.
- Visualização de gráficos interativos (linha, área e candlestick).
- Cálculo de retornos percentuais para janelas de 30, 90 e 365 dias.

## Tecnologias usadas

- Python
- Streamlit
- yFinance
- Plotly

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

## Exemplo de uso

1. Selecione o mercado (Brasil ou EUA).
2. Insira o código do ativo (ex.: `PETR4` ou `AAPL`).
3. Escolha o período e o tipo de gráfico.
4. Clique em "Buscar" para visualizar os dados e gráficos.

## Próximos passos

- Adicionar múltiplos ativos simultâneos.
- Implementar comparações visuais entre ativos.
- Adicionar filtros de datas e indicadores técnicos.
