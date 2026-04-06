import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def predict_future(symbol, future_days):
    df = yf.download(symbol, period="10y")
    if df.empty or len(df) < 100: return None

    # Syncing column names to avoid trainer errors
    prices = df[['Close']].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(prices)

    X, y = [], []
    window = 60 # 60 days of memory
    for i in range(window, len(scaled_data)):
        X.append(scaled_data[i-window:i, 0])
        y.append(scaled_data[i, 0])
    
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # Improved LSTM Architecture
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)),
        Dropout(0.2),
        LSTM(units=50),
        Dropout(0.2),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=10, batch_size=32, verbose=0)

    # Predicting Future Days
    last_60_days = scaled_data[-window:]
    current_batch = last_60_days.reshape((1, window, 1))
    future_preds = []

    for _ in range(future_days):
        next_pred = model.predict(current_batch, verbose=0)
        future_preds.append(next_pred[0, 0])
        current_batch = np.append(current_batch[:, 1:, :], [[next_pred[0]]], axis=1)

    final_prices = scaler.inverse_transform(np.array(future_preds).reshape(-1, 1))
    dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=future_days)
    
    return pd.DataFrame({"Date": dates.date, "Predicted Price": final_prices.flatten().round(2)})