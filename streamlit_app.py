import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import ta

# 페이지 설정
st.set_page_config(page_title="주식 차트 분석", layout="wide")

# 제목
st.title("📈 주식 차트 분석 도구")

# 사이드바 설정
st.sidebar.header("설정")

# 티커 입력
ticker = st.sidebar.text_input("티커 입력", value="AAPL", help="예: AAPL, GOOGL, TSLA, 005930.KS")

# 차트 기간 선택
period_options = {
    "일봉 (3개월)": ("1d", "3mo"),
    "주봉 (9개월)": ("1wk", "9mo"),
    "월봉 (10년)": ("1mo", "10y")
}

selected_period = st.sidebar.radio("차트 기간 선택", list(period_options.keys()))

# 보조지표 선택
indicators = st.sidebar.multiselect(
    "보조지표 선택",
    ["거래량", "MACD", "RSI", "Williams %R", "Bollinger Bands"],
    default=["거래량", "MACD", "RSI"]
)

def get_stock_data(ticker, interval, period):
    """주식 데이터 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(interval=interval, period=period)
        return data
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

def calculate_indicators(data):
    """보조지표 계산"""
    # MACD
    macd_line, macd_signal, macd_histogram = ta.trend.MACD(data['Close']).macd(), ta.trend.MACD(data['Close']).macd_signal(), ta.trend.MACD(data['Close']).macd_diff()
    
    # RSI
    rsi = ta.momentum.RSIIndicator(data['Close']).rsi()
    
    # Williams %R
    williams_r = ta.momentum.WilliamsRIndicator(data['High'], data['Low'], data['Close']).williams_r()
    
    # Bollinger Bands
    bb_upper = ta.volatility.BollingerBands(data['Close']).bollinger_hband()
    bb_middle = ta.volatility.BollingerBands(data['Close']).bollinger_mavg()
    bb_lower = ta.volatility.BollingerBands(data['Close']).bollinger_lband()
    
    return {
        'macd_line': macd_line,
        'macd_signal': macd_signal,
        'macd_histogram': macd_histogram,
        'rsi': rsi,
        'williams_r': williams_r,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower
    }

def create_chart(data, indicators_data, selected_indicators, ticker):
    """차트 생성"""
    # 서브플롯 개수 계산
    subplot_count = 1  # 메인 차트
    if "거래량" in selected_indicators:
        subplot_count += 1
    if "MACD" in selected_indicators:
        subplot_count += 1
    if "RSI" in selected_indicators:
        subplot_count += 1
    if "Williams %R" in selected_indicators:
        subplot_count += 1
    
    # 서브플롯 생성
    subplot_titles = [f"{ticker} 주가"]
    if "거래량" in selected_indicators:
        subplot_titles.append("거래량")
    if "MACD" in selected_indicators:
        subplot_titles.append("MACD")
    if "RSI" in selected_indicators:
        subplot_titles.append("RSI")
    if "Williams %R" in selected_indicators:
        subplot_titles.append("Williams %R")
    
    fig = make_subplots(
        rows=subplot_count,
        cols=1,
        subplot_titles=subplot_titles,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_width=[0.7] + [0.3] * (subplot_count - 1)
    )
    
    # 캔들스틱 차트
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="주가"
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    if "Bollinger Bands" in selected_indicators:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(250,128,114,0.5)', width=1)
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color='rgba(255,165,0,0.8)', width=1)
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(250,128,114,0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(250,128,114,0.1)'
            ),
            row=1, col=1
        )
    
    current_row = 2
    
    # 거래량
    if "거래량" in selected_indicators:
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name="거래량",
                marker_color='rgba(158,202,225,0.8)'
            ),
            row=current_row, col=1
        )
        current_row += 1
    
    # MACD
    if "MACD" in selected_indicators:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['macd_line'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['macd_signal'],
                mode='lines',
                name='Signal',
                line=dict(color='red', width=2)
            ),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=indicators_data['macd_histogram'],
                name='Histogram',
                marker_color='green'
            ),
            row=current_row, col=1
        )
        current_row += 1
    
    # RSI
    if "RSI" in selected_indicators:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=current_row, col=1
        )
        # RSI 과매수/과매도 선
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
        current_row += 1
    
    # Williams %R
    if "Williams %R" in selected_indicators:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators_data['williams_r'],
                mode='lines',
                name='Williams %R',
                line=dict(color='orange', width=2)
            ),
            row=current_row, col=1
        )
        # Williams %R 과매수/과매도 선
        fig.add_hline(y=-20, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
        current_row += 1
    
    # 레이아웃 설정
    fig.update_layout(
        title=f"{ticker} 주식 차트",
        xaxis_title="날짜",
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

# 메인 로직
if ticker:
    # 데이터 가져오기
    interval, period = period_options[selected_period]
    
    with st.spinner("데이터를 불러오는 중..."):
        data = get_stock_data(ticker, interval, period)
    
    if data is not None and not data.empty:
        # 주식 정보 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("현재가", f"${data['Close'].iloc[-1]:.2f}")
        
        with col2:
            change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
            change_pct = (change / data['Close'].iloc[-2]) * 100
            st.metric("전일 대비", f"${change:.2f}", f"{change_pct:.2f}%")
        
        with col3:
            st.metric("거래량", f"{data['Volume'].iloc[-1]:,.0f}")
        
        with col4:
            st.metric("기간", selected_period)
        
        # 보조지표 계산
        indicators_data = calculate_indicators(data)
        
        # 차트 생성 및 표시
        chart = create_chart(data, indicators_data, indicators, ticker)
        st.plotly_chart(chart, use_container_width=True)
        
        # 최근 데이터 표시
        st.subheader("최근 데이터")
        st.dataframe(data.tail(10))
        
        # 기술적 분석 요약
        st.subheader("기술적 분석 요약")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "RSI" in indicators:
                current_rsi = indicators_data['rsi'].iloc[-1]
                if current_rsi > 70:
                    rsi_signal = "과매수"
                elif current_rsi < 30:
                    rsi_signal = "과매도"
                else:
                    rsi_signal = "중립"
                st.write(f"**RSI**: {current_rsi:.2f} ({rsi_signal})")
        
        with col2:
            if "Williams %R" in indicators:
                current_wr = indicators_data['williams_r'].iloc[-1]
                if current_wr > -20:
                    wr_signal = "과매수"
                elif current_wr < -80:
                    wr_signal = "과매도"
                else:
                    wr_signal = "중립"
                st.write(f"**Williams %R**: {current_wr:.2f} ({wr_signal})")
        
    else:
        st.error("데이터를 불러올 수 없습니다. 티커를 확인해주세요.")
else:
    st.info("사이드바에서 티커를 입력해주세요.")

# 사용법 안내
with st.expander("사용법 안내"):
    st.write("""
    **티커 입력 예시:**
    - 미국 주식: AAPL, GOOGL, TSLA, MSFT
    - 한국 주식: 005930.KS (삼성전자), 000660.KS (SK하이닉스)
    - 기타 국가: 티커 뒤에 해당 국가 코드 추가
    
    **차트 기간:**
    - 일봉: 3개월간의 일간 데이터
    - 주봉: 9개월간의 주간 데이터  
    - 월봉: 10년간의 월간 데이터
    
    **보조지표:**
    - 거래량: 해당 기간의 거래량
    - MACD: 이동평균수렴확산
    - RSI: 상대강도지수 (70 이상 과매수, 30 이하 과매도)
    - Williams %R: 윌리엄스 %R (-20 이상 과매수, -80 이하 과매도)
    - Bollinger Bands: 볼린저 밴드
    """)