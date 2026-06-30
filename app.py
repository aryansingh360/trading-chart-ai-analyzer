import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

class PremiumTradingAnalyzer:
    def __init__(self, ticker, period="1y", interval="1d"):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.df = None
        self.load_data()
    
    def load_data(self):
        self.df = yf.download(self.ticker, period=self.period, interval=self.interval)
        self.df.dropna(inplace=True)
        print(f"Loaded {len(self.df)} candles for {self.ticker}")
    
    def add_indicators(self):
        # Add extensive indicators via pandas_ta
        self.df.ta.strategy()  # Common strategy - adds many indicators
        # Additional custom
        self.df['ATR'] = ta.atr(self.df['High'], self.df['Low'], self.df['Close'], length=14)
        self.df['RSI'] = ta.rsi(self.df['Close'], length=14)
        self.df['MACD'] = ta.macd(self.df['Close'])['MACD_12_26_9']
        self.df['BB_upper'], self.df['BB_middle'], self.df['BB_lower'] = ta.bbands(self.df['Close']).iloc[:, [0,1,2]].T.values
        self.df['SMA_50'] = ta.sma(self.df['Close'], length=50)
        self.df['SMA_200'] = ta.sma(self.df['Close'], length=200)
        self.df['EMA_20'] = ta.ema(self.df['Close'], length=20)
        
        # Candlestick patterns (many via pandas_ta)
        self.df.ta.cdl_pattern(append=True)  # Adds many CDL_ patterns
        
        self.df.dropna(inplace=True)
    
    def detect_support_resistance(self, window=20):
        """Simple but effective swing-based S/R detection"""
        highs = self.df['High'].rolling(window=window, center=True).max()
        lows = self.df['Low'].rolling(window=window, center=True).min()
        
        resistance_levels = highs[highs == self.df['High']].dropna().unique()[-5:]  # Recent
        support_levels = lows[lows == self.df['Low']].dropna().unique()[-5:]
        
        return sorted(support_levels, reverse=False)[-3:], sorted(resistance_levels, reverse=True)[:3]
    
    def fibonacci_levels(self):
        """Fib retracement from recent swing high/low"""
        recent_high = self.df['High'].tail(60).max()
        recent_low = self.df['Low'].tail(60).min()
        diff = recent_high - recent_low
        levels = {}
        fib_ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        for ratio in fib_ratios:
            levels[f"Fib_{int(ratio*100)}"] = recent_low + diff * ratio
        return levels
    
    def ml_predict(self):
        """Simple but powerful RF classifier for next candle direction"""
        df_ml = self.df.copy()
        df_ml['Target'] = (df_ml['Close'].shift(-1) > df_ml['Close']).astype(int)
        
        features = [col for col in df_ml.columns if col not in ['Target', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
        X = df_ml[features].iloc[:-1]
        y = df_ml['Target'].iloc[:-1]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(X_train, y_train)
        
        pred = model.predict(X_test)
        acc = accuracy_score(y_test, pred)
        print(f"ML Model Accuracy (direction): {acc:.2%}")
        
        latest_features = df_ml[features].iloc[-1:].fillna(0)
        next_pred = model.predict(latest_features)[0]
        prob = model.predict_proba(latest_features)[0][next_pred]
        return "Bullish" if next_pred == 1 else "Bearish", prob
    
    def suggest_sl_tp(self, entry_price=None, risk_percent=1.0):
        """Dynamic ATR-based SL/TP with Fib & S/R confluence"""
        if entry_price is None:
            entry_price = self.df['Close'].iloc[-1]
        
        atr = self.df['ATR'].iloc[-1]
        supports, resistances = self.detect_support_resistance()
        
        # SL: Below nearest support or ATR multiple
        sl = entry_price - 1.5 * atr
        for sup in supports:
            if sup < entry_price and sup > sl:
                sl = sup * 0.999  # slight buffer
        
        # TP: Multiple of risk, nearest resistance, or Fib
        risk = entry_price - sl
        tp1 = entry_price + 2 * risk   # 1:2 RR
        tp2 = entry_price + 3 * risk   # 1:3 RR
        
        fibs = self.fibonacci_levels()
        for level in fibs.values():
            if level > entry_price and level < tp2:
                tp2 = level
        
        for res in resistances:
            if res > entry_price and res < tp2:
                tp2 = res * 1.001
        
        return {
            "Entry": round(entry_price, 4),
            "Stop Loss": round(sl, 4),
            "Take Profit 1 (2R)": round(tp1, 4),
            "Take Profit 2 (3R)": round(tp2, 4),
            "Risk %": round(risk_percent, 2),
            "Potential Reward/Risk": "1:2 to 1:3+"
        }
    
    def analyze(self):
        self.add_indicators()
        trend, prob = self.ml_predict()
        sl_tp = self.suggest_sl_tp()
        supports, resistances = self.detect_support_resistance()
        fibs = self.fibonacci_levels()
        
        print("\n" + "="*60)
        print(f"PREMIUM ANALYSIS REPORT for {self.ticker} - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*60)
        print(f"Current Price: {self.df['Close'].iloc[-1]:.4f}")
        print(f"Overall Trend Signal (ML): {trend} (Confidence: {prob:.1%})")
        print("\nKey Indicators:")
        print(f"RSI: {self.df['RSI'].iloc[-1]:.2f} {'(Overbought)' if self.df['RSI'].iloc[-1] > 70 else '(Oversold)' if self.df['RSI'].iloc[-1] < 30 else '(Neutral)'}")
        print(f"MACD: {self.df['MACD'].iloc[-1]:.4f}")
        print(f"Price vs SMA200: {'Above (Bullish)' if self.df['Close'].iloc[-1] > self.df['SMA_200'].iloc[-1] else 'Below (Bearish)'}")
        
        print("\nSupport Levels:", [round(s,4) for s in supports])
        print("Resistance Levels:", [round(r,4) for r in resistances])
        print("\nFibonacci Retracement Levels (Recent Swing):")
        for k, v in fibs.items():
            print(f"  {k}: {v:.4f}")
        
        print("\nRecommended Trade Setup (Long example):")
        for k, v in sl_tp.items():
            print(f"  {k}: {v}")
        
        print("\nSmart Insights:")
        print("- Look for confluence: Price near S/R + Fib + indicator alignment.")
        print("- Volume confirmation recommended for breakouts.")
        print("- Risk only 1% of capital per trade. Use position sizing.")
        print("- This is NOT financial advice. Backtest thoroughly.")
        
        # Visualization
        self.plot_chart()
    
    def plot_chart(self):
        adps = [mpf.make_addplot(self.df['SMA_50'], color='orange'),
                mpf.make_addplot(self.df['SMA_200'], color='blue'),
                mpf.make_addplot(self.df['BB_upper'], color='gray', linestyle='--'),
                mpf.make_addplot(self.df['BB_lower'], color='gray', linestyle='--')]
        
        mpf.plot(self.df.tail(120), type='candle', style='charles',
                 title=f"{self.ticker} Premium Chart",
                 addplot=adps, volume=True, figsize=(12,8),
                 savefig=f"{self.ticker}_analysis.png")
        print(f"Chart saved as {self.ticker}_analysis.png")

# Usage Example
if __name__ == "__main__":
    analyzer = PremiumTradingAnalyzer("AAPL", period="6mo", interval="1d")  # Change ticker/symbol
    analyzer.analyze()
