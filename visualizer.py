import plotly.graph_objects as go

def plot_price_history(data, ticker: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name=ticker))
    fig.update_layout(
        title=f'Histórico de Preços - {ticker}',
        xaxis_title='Data',
        yaxis_title='Preço de Fechamento',
        template='plotly_white'
    )
    return fig