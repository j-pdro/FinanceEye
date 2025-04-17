import yfinance as yf

def fetch_data(ticker: str, period: str = '6mo'):
    try:
        data = yf.download(ticker, period=period)
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None

def fetch_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    if data.empty:
        raise ValueError(f"Nenhum dado encontrado para o ativo '{ticker}'. Verifique se ele existe.")
    return data
