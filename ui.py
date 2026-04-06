import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
from predictor import predict_future
from news_fetcher import fetch_news


# =========================================================
# 1. PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Stock Prophet 2026", layout="wide")


# =========================================================
# 2. SESSION MEMORY (APP STATE)
# =========================================================
if "app_store" not in st.session_state:
    st.session_state.app_store = {
        "hist_df": None,
        "pred_df": None,
        "hist_metrics": None,
        "pred_metrics": None,
        "chat_log": []
    }

# Gemini chat session holder
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None


# =========================================================
# 3. 🤖 GEMINI AI MARKET STRATEGIST (FIXED VERSION)
# =========================================================
def run_ai_buddy():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI Market Strategist")

    key = st.secrets.get("GEMINI_API_KEY")

    if not key:
        st.sidebar.error("🔑 GEMINI_API_KEY missing in .streamlit/secrets.toml")
        return

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-flash-latest")

    # ✅ Create chat session once (persistent memory)
    if st.session_state.gemini_chat is None:
        st.session_state.gemini_chat = model.start_chat(history=[])

    chat_box = st.sidebar.container(height=300)

    # Show old messages
    for msg in st.session_state.app_store["chat_log"]:
        chat_box.chat_message(msg["role"]).write(msg["content"])

    prompt = st.sidebar.chat_input("Ask about the stock...")

    if prompt:
        st.session_state.app_store["chat_log"].append(
            {"role": "user", "content": prompt}
        )

        try:
            with st.spinner("Thinking..."):
                response = st.session_state.gemini_chat.send_message(prompt)

            reply = response.text

            st.session_state.app_store["chat_log"].append(
                {"role": "assistant", "content": reply}
            )

            st.rerun()

        except Exception as e:
            st.sidebar.error(f"Gemini Error: {str(e)}")


# =========================================================
# 4. MAIN APP
# =========================================================
def launch_app():

    st.title("📈 Stock Analysis & Future Prediction")

    # ------------------ SIDEBAR CONTROLS ------------------
    with st.sidebar:
        st.header("⚙️ Controls")

        ticker = st.text_input("Enter Ticker", "AAPL").upper()

        st.markdown("### 📊 Historical Analysis")
        h_years = st.slider("History Range (Years)", 1, 20, 5)
        btn_hist = st.button("Analyze History", use_container_width=True)

        st.markdown("### 🔮 Prediction Calculus")
        p_months = st.slider("Forecast Range (Months)", 1, 600, 12)
        btn_pred = st.button("Predict Future", use_container_width=True)

        if st.button("🗑️ Clear Chat"):
            st.session_state.app_store["chat_log"] = []
            st.session_state.gemini_chat = None
            st.rerun()

    # Run chatbot
    run_ai_buddy()

    col1, col2 = st.columns([3, 1.2])

    # =====================================================
    # LEFT SIDE (ANALYSIS + PREDICTION)
    # =====================================================
    with col1:

        # ================= HISTORICAL =================
        if btn_hist:
            with st.spinner("Fetching historical data..."):
                try:
                    df = yf.download(ticker, period=f"{h_years}y")

                    s_price = float(df["Close"].iloc[0])
                    e_price = float(df["Close"].iloc[-1])
                    growth = ((e_price - s_price) / s_price) * 100

                    st.session_state.app_store["hist_df"] = df
                    st.session_state.app_store["hist_metrics"] = (s_price, e_price, growth)

                except Exception as e:
                    st.error(e)

        if st.session_state.app_store["hist_metrics"]:
            s, e, g = st.session_state.app_store["hist_metrics"]

            st.subheader(f"📊 Historical Analysis: {ticker}")

            m1, m2, m3 = st.columns(3)
            m1.metric(f"Price {h_years}y Ago", f"${s:.2f}")
            m2.metric("Latest Close", f"${e:.2f}")
            m3.metric("Total Growth", f"{g:.2f}%", delta=f"{g:.2f}%")

            st.line_chart(st.session_state.app_store["hist_df"]["Close"])

            with st.expander("📂 View History Table"):
                st.dataframe(
                    st.session_state.app_store["hist_df"],
                    use_container_width=True
                )

        # ================= PREDICTION =================
        if btn_pred:
            with st.spinner("AI Calculating predictions..."):
                try:
                    p_days = int(p_months * 30.44)

                    pdf = predict_future(ticker, p_days)

                    curr_p = float(yf.download(ticker, period="1d")["Close"].iloc[-1])
                    target_p = float(pdf["Predicted Price"].iloc[-1])

                    change_p = ((target_p - curr_p) / curr_p) * 100

                    st.session_state.app_store["pred_df"] = pdf
                    st.session_state.app_store["pred_metrics"] = (
                        curr_p, target_p, change_p
                    )

                except Exception as e:
                    st.error(e)

        if st.session_state.app_store["pred_metrics"]:
            cp, tp, ch = st.session_state.app_store["pred_metrics"]

            st.subheader(f"🔮 Future Forecast ({p_months} Months)")

            p1, p2, p3 = st.columns(3)
            p1.metric("Current Price", f"${cp:.2f}")
            p2.metric("Target Price", f"${tp:.2f}")
            p3.metric("Net Change", f"{ch:.2f}%", delta=f"{ch:.2f}%")

            st.line_chart(
                st.session_state.app_store["pred_df"].set_index("Date")
            )

            with st.expander("📂 View Prediction Table"):
                st.dataframe(
                    st.session_state.app_store["pred_df"],
                    use_container_width=True
                )

    # =====================================================
    # RIGHT SIDE (NEWS)
    # =====================================================
    with col2:
        st.subheader("📰 Market Reels")

        news_data = fetch_news(ticker)

        if news_data:
            for n in news_data[:8]:
                with st.container(border=True):
                    st.markdown(f"**{n['title']}**")
                    st.caption(f"Source: {n['source']}")
                    st.page_link(n["url"], label="Read Full Reel", icon="🔗")
        else:
            st.info("Searching for news...")


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    launch_app()
