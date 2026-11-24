import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title='BTC Trading Terminal', page_icon='₿', layout='wide')
st.title('₿ Bitcoin Trading Terminal')
st.caption('Coinbase Exchange • BTC/USD • Market monitoring only')
BASE = 'https://api.exchange.coinbase.com/products/BTC-USD'
FRAMES = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600, '6h': 21600, '1D': 86400}
with st.sidebar:
    frame = st.selectbox('Timeframe', list(FRAMES), index=1)
    count = st.slider('Visible candles', 30, 200, 100)
    ema20 = st.checkbox('EMA 20', True)
    ema50 = st.checkbox('EMA 50', True)
    refresh = st.checkbox('Auto refresh (10 seconds)', True)
    st.caption('All chart times are UTC. The newest candle may still be forming.')

@st.cache_data(ttl=30, show_spinner=False)
def candles(seconds):
    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=seconds*280)
    r = requests.get(BASE+'/candles', params={'granularity': seconds, 'start':start.isoformat(), 'end':end.isoformat()}, timeout=10)
    r.raise_for_status()
    df = pd.DataFrame(r.json(), columns=['Time','Low','High','Open','Close','Volume'])
    if df.empty:
        raise ValueError('No candles returned')
    df['Time'] = pd.to_datetime(df['Time'], unit='s', utc=True)
    df = df.sort_values('Time').drop_duplicates('Time')
    for col in ['Low','High','Open','Close','Volume']:
        df[col] = pd.to_numeric(df[col], errors='raise')
    for n in [20,50]:
        df[f'EMA {n}'] = df['Close'].ewm(span=n, adjust=False, min_periods=n).mean()
    return df

@st.fragment(run_every='10s' if refresh else None)
def dashboard():
    try:
        r = requests.get(BASE+'/ticker', timeout=10)
        r.raise_for_status()
        ticker = r.json()
        price = float(ticker['price'])
        df = candles(FRAMES[frame]).copy()
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        st.error(f'Market data unavailable: {e}')
        return
    # Live ticker is distinct from the cached exchange candle data.
    visible = df.tail(count)
    a,b,c,d = st.columns(4)
    a.metric('Latest trade', f'${price:,.2f}')
    b.metric('Chart high', f'${visible.High.max():,.2f}')
    c.metric('Chart low', f'${visible.Low.min():,.2f}')
    d.metric('24h volume (BTC)', f'{float(ticker["volume"]):,.2f}' if 'volume' in ticker else 'N/A')
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.78,.22], vertical_spacing=.04)
    fig.add_trace(go.Candlestick(x=visible.Time, open=visible.Open, high=visible.High, low=visible.Low, close=visible.Close, name='BTC/USD', increasing_line_color='#22c55e', decreasing_line_color='#ef4444'), row=1,col=1)
    for n, show, color in [(20,ema20,'#f59e0b'),(50,ema50,'#38bdf8')]:
        if show:
            fig.add_trace(go.Scatter(x=visible.Time,y=visible[f'EMA {n}'],name=f'EMA {n}',line=dict(color=color,width=1.5)),row=1,col=1)
    colors = ['#22c55e' if c>=o else '#ef4444' for o,c in zip(visible.Open,visible.Close)]
    fig.add_trace(go.Bar(x=visible.Time,y=visible.Volume,marker_color=colors,name='Volume (BTC)'),row=2,col=1)
    fig.update_layout(template='plotly_dark',height=650,xaxis_rangeslider_visible=False,margin=dict(l=10,r=10,t=35,b=10),legend=dict(orientation='h'),uirevision=frame)
    fig.update_yaxes(title_text='USD',row=1,col=1,side='right')
    fig.update_yaxes(title_text='BTC',row=2,col=1,side='right')
    st.plotly_chart(fig,use_container_width=True,config={'scrollZoom':True})
    st.caption(f'Ticker trade time: {ticker.get("time", "Unavailable")} | Candle data cached for 30 seconds; ticker checked every 10 seconds when auto refresh is enabled.')
    st.subheader('Recent OHLCV data')
    st.dataframe(visible.tail(10).iloc[::-1],use_container_width=True,hide_index=True)
    st.download_button('Download displayed candles (CSV)',visible.to_csv(index=False),'btc_candles.csv','text/csv')

dashboard()
