import requests
import streamlit as st

def fetch_news(symbol):
    api_key = st.secrets.get("NEWS_API_KEY")
    if not api_key: return []

    url = f"https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&pageSize=15&apiKey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a["title"],
                "url": a["url"],
                "source": a["source"]["name"]
            })
        return articles
    except:
        return []