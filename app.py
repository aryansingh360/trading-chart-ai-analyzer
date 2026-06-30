import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import logging
import warnings
from sklearn.model_selection import train_test_split
import xgboost as xgb
from scipy.signal import find_peaks

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UltraPremiumAnalyzer:
    def __init__(self, ticker, period="1y"):
        self.ticker = ticker.upper()
        self.period = period
        self.data = {}  # Multi-timeframe cache
        self.load_multi_tf_data()
    
    def load_multi_tf_data(self):
        intervals = ['1d', '1h', '15m']
        for interval in intervals:
            try:
                df = yf.download(self.ticker, period=self.period, interval=interval, progress=False)
                df = df.dropna()
                if len(df) < 50:
                    logging.warning(f"Insufficient data for {interval}")
                    continue
                self.data[interval] = df
                logging.info(f"Loaded {len(df)} candles for {interval}")
            except Exception as e:
                logging.error(f"Failed to load {interval}: {e}")
    
    def add_indicators(self, df):
        try:
            df = df.copy()
            # Efficient indicator batch
            df.ta.strategy("Common")  # Core indicators
            df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            bb = ta.bbands(df['Close'])
            df = pd.concat([df, bb], axis=1)
            
            # Candlestick patterns (selective)
            patterns = df.ta.cdl_pattern(append=True)
            if patterns is not None:
                df = pd.concat([df, patterns], axis=1)
            
            return df.dropna()
        except Exception as e:
            logging.error(f"Indicator error: {e}")
            return df
    
    def detect_support_resistance(self, df, n_peaks=5):
        """Improved: Peak detection + proximity grouping"""
        prices = df['Close'].values
        # Find peaks and troughs
        peaks, _ = find_peaks(prices, distance=10)
        troughs, _ = find_peaks(-prices, distance=10)
        
        resistance = np.sort(prices[peaks])[-n_peaks:] if len(peaks) > 0 else []
        support = np.sort(prices[troughs])[:n_peaks] if len(troughs) > 0 else []
        
        # Simple clustering (group close levels)
        def cluster_levels(levels, tol=0.005):
            if len(levels) == 0: return []
            clustered = []
            for lvl in sorted(levels):
                if not clustered or abs(lvl - clustered[-1]) / clustered[-1] > tol:
                    clustered.append(lvl)
            return clustered[-3:]  # Top recent
        
        return cluster_levels(support), cluster_levels(resistance)
    
    def fibonacci_levels(self, df):
        recent_high = df['High'].tail(90).max()
        recent_low = df['Low'].tail(90).min()
        diff = recent_high - recent_low
        ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618]
        return {f"Fib_{int(r*100)}": round(recent_low + diff * r, 4) for r in ratios}
    
    def ml_predict(self, df):
        """XGBoost with feature importance"""
        df_ml = df.copy()
        df_ml['Target'] = (df_ml['Close'].shift(-1) > df_ml['Close']).astype(int)
        
        feature_cols = [col for col in df_ml.columns if col not in 
                       ['Target', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
        
        X = df_ml[feature_cols].iloc[:-1].fillna(0)
        y = df_ml['Target'].iloc[:-1]
        
        if len(X) < 100:
            return "Neutral", 0.5, {}
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, shuffle=False)
        
        model = xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, 
                                 subsample=0.8, colsample_bytree=0.8, random_state=42)
        model.fit(X_train, y_train)
        
        pred_prob = model.predict_proba(X.iloc[-1:].fillna(0))[0]
        direction = "Bullish" if pred_prob[1] > 0.55 else "Bearish" if pred_prob[0] > 0.55 else "Neutral"
        
        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return direction, max(pred_prob), top_features
    
    def get_confluence_score(self, df, signal):
        """Multi-factor confidence score"""
        score = 50
        rsi = df['RSI'].iloc[-1]
        if (signal == "Bullish" and rsi < 70) or (signal == "Bearish" and rsi > 30):
            score += 15
        if 'MACD_12_26_9' in df.columns:
            macd = df['MACD_12_26_9'].iloc[-1]
            if (signal == "Bullish" and macd > 0) or (signal == "Bearish" and macd < 0):
                score += 15
        # Add more factors as needed
        return min(95, max(30, int(score)))
    
    def suggest_sl_tp(self, df, entry=None):
        if entry is None:
            entry = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1]
        
        sl = entry - 1.8 * atr   # Dynamic ATR
        tp1 = entry + 2.0 * (entry - sl)
        tp2 = entry + 3.5 * (entry - sl)
        
        supports, resistances = self.detect_support_resistance(df)
        for s in supports:
            if entry - 3*atr < s < entry:
                sl = max(sl, s * 0.998)
        for r in resistances:
            if entry < r < entry + 5*atr:
                tp2 = min(tp2, r * 1.002)
        
        return {
            "Entry": round(entry, 4),
            "Stop Loss": round(sl, 4),
            "TP1 (2R)": round(tp1, 4),
            "TP2 (3.5R)": round(tp2, 4),
            "Trailing Stop": f"Trail after {round(2*atr,4)} profit"
        }
    
    def analyze(self):
        if not self.data:
            print("No data loaded!")
            return
        
        main_df = self.add_indicators(self.data.get('1d', pd.DataFrame()))
        if main_df.empty:
            print("Insufficient data.")
            return
        
        direction, prob, top_feat = self.ml_predict(main_df)
        score = self.get_confluence_score(main_df, direction)
        sl_tp = self.suggest_sl_tp(main_df)
        sup, res = self.detect_support_resistance(main_df)
        fibs = self.fibonacci_levels(main_df)
        
        print("\n" + "="*70)
        print(f"ULTRA PREMIUM ANALYSIS - {self.ticker} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)
        print(f"Current Price: {main_df['Close'].iloc[-1]:.4f}")
        print(f"ML Signal: {direction} | Confidence: {prob:.1%} | Confluence Score: {score}/100")
        
        print("\nMulti-Timeframe Alignment:")
        for tf, df_tf in self.data.items():
            if not df_tf.empty:
                tf_dir = "Bullish" if df_tf['Close'].iloc[-1] > df_tf['Close'].iloc[-20] else "Bearish"
                print(f"  {tf.upper()}: {tf_dir}")
        
        print("\nSupport:", [round(x,4) for x in sup])
        print("Resistance:", [round(x,4) for x in res])
        print("\nKey Fibonacci Levels:", list(fibs.items())[:6])
        
        print("\nRecommended Setup:")
        for k, v in sl_tp.items():
            print(f"  {k}: {v}")
        
        print("\nTop ML Features:", list(top_feat.keys())[:3])
        print("\nAdvice: Prioritize higher-timeframe alignment. Use <1% risk per trade.")
        
        self.plot_interactive(main_df)
    
    def plot_interactive(self, df):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                           row_heights=[0.5, 0.2, 0.3], vertical_spacing=0.05)
        
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                    low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA50", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name="SMA200", line=dict(color='blue')), row=1, col=1)
        
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=3, col=1)
        
        fig.update_layout(title=f"{self.ticker} Ultra Analysis", height=900, xaxis_rangeslider_visible=False)
        fig.write_html(f"{self.ticker}_interactive.html")
        print(f"Interactive chart saved: {self.ticker}_interactive.html")
        # fig.show()  # Uncomment for immediate view

# Usage
if __name__ == "__main__":
    analyzer = UltraPremiumAnalyzer("AAPL", period="9mo")  # or "BTC-USD"
    analyzer.analyze()
