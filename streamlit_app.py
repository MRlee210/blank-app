import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Streamlit 앱 제목 설정
st.title('주식 차트 조회 📈')

# Ticker 입력 받기
ticker = st.text_input('Ticker를 입력하세요 (예: AAPL, GOOG)', 'AAPL')

# 기간 선택 버튼
st.write("차트 기간을 선택하세요:")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button('일봉 (3개월)'):
        period = "3mo"
        interval = "1d"
with col2:
    if st.button('주봉 (9개월)'):
        period = "9mo"
        interval = "1wk"
with col3:
    if st.button('월봉 (10년)'):
        period = "10y"
        interval = "1mo"

# 데이터 불러오기 및 차트 생성
if 'period' in locals():
    try:
        # yfinance를 통해 데이터 다운로드
        data = yf.download(ticker, period=period, interval=interval)

        if not data.empty:
            # 보조 지표 계산
            # 거래량
            volume = data['Volume']

            # MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()

            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Williams %R
            high_14 = data['High'].rolling(14).max()
            low_14 = data['Low'].rolling(14).min()
            williams_r = -100 * ((high_14 - data['Close']) / (high_14 - low_14))

            # Bollinger Bands
            ma20 = data['Close'].rolling(window=20).mean()
            std20 = data['Close'].rolling(window=20).std()
            upper_band = ma20 + std20 * 2
            lower_band = ma20 - std20 * 2

            # Plotly를 사용하여 차트 생성
            fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                                row_heights=[0.5, 0.1, 0.1, 0.1, 0.1])

            # 1. 주가 및 볼린저 밴드 차트
            fig.add_trace(go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'],
                                         name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=upper_band, mode='lines', name='Upper Band',
                                     line={'color': 'rgba(255, 165, 0, 0.5)'}), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=lower_band, mode='lines', name='Lower Band',
                                     line={'color': 'rgba(255, 165, 0, 0.5)'}), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=ma20, mode='lines', name='20일 이동평균',
                                     line={'color': 'rgba(0, 0, 255, 0.5)'}), row=1, col=1)


            # 2. 거래량 차트
            fig.add_trace(go.Bar(x=data.index, y=volume, name='거래량'), row=2, col=1)

            # 3. MACD 차트
            fig.add_trace(go.Scatter(x=data.index, y=macd, name='MACD', line={'color': 'blue'}), row=3, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=signal, name='Signal Line', line={'color': 'red'}), row=3, col=1)

            # 4. RSI 차트
            fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI'), row=4, col=1)
            fig.add_hline(y=70, row=4, col=1, line_dash="dash", line_color="red")
            fig.add_hline(y=30, row=4, col=1, line_dash="dash", line_color="blue")


            # 5. Williams %R 차트
            fig.add_trace(go.Scatter(x=data.index, y=williams_r, name='Williams %R'), row=5, col=1)
            fig.add_hline(y=-20, row=5, col=1, line_dash="dash", line_color="red")
            fig.add_hline(y=-80, row=5, col=1, line_dash="dash", line_color="blue")


            # 차트 레이아웃 업데이트
            fig.update_layout(
                title=f'{ticker} 주식 차트',
                height=800,
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="가격", row=1, col=1)
            fig.update_yaxes(title_text="거래량", row=2, col=1)
            fig.update_yaxes(title_text="MACD", row=3, col=1)
            fig.update_yaxes(title_text="RSI", row=4, col=1)
            fig.update_yaxes(title_text="Williams %R", row=5, col=1)


            # Streamlit에 차트 표시
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("해당 Ticker의 데이터를 불러올 수 없습니다. Ticker를 확인해주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")