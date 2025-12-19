from flask import Flask, request, render_template_string
import json
import time
import os
import requests
from bs4 import BeautifulSoup  # This tool helps us read the web

app = Flask(__name__)

# 1. Load Internal Index
INDEX_FILE = "inverted_index.json"
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# 2. The Dark Stealth UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini-Google | Global</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        :root {
            --bg-color: #0a0a0a; --card-bg: rgba(25, 25, 25, 0.85); --text-primary: #ffffff;
            --text-secondary: #a0a0a0; --accent-color: #00f2ff;
            --accent-gradient: linear-gradient(135deg, #00c6ff, #0072ff);
        }
        body { 
            font-family: 'Inter', sans-serif; background-color: var(--bg-color);
            background-image: radial-gradient(circle at 20% 30%, rgba(0, 242, 255, 0.05) 0%, transparent 50%),
                              radial-gradient(circle at 80% 70%, rgba(188, 19, 254, 0.05) 0%, transparent 50%);
            min-height: 100vh; margin: 0; display: flex; flex-direction: column; align-items: center; color: var(--text-primary);
        }
        h1 { font-weight: 800; font-size: 3.5rem; margin-top: 60px; letter-spacing: -1px;
            background: linear-gradient(to right, #fff, #a0a0a0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        h1 span { color: var(--accent-color); -webkit-text-fill-color: var(--accent-color); }
        .container {
            background: var(--card-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 50px; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4); width: 85%; max-width: 650px; text-align: center;
        }
        input { padding: 18px 25px; width: 65%; border-radius: 14px; border: 2px solid rgba(255, 255, 255, 0.1); background: rgba(0,0,0,0.3); color: white; font-size: 17px; outline: none; }
        input:focus { border-color: var(--accent-color); box-shadow: 0 0 20px rgba(0, 242, 255, 0.2); }
        button { padding: 18px 35px; background: var(--accent-gradient); color: white; border: none; border-radius: 14px; font-size: 17px; font-weight: 700; cursor: pointer; }
        .result-card { background: rgba(35, 35, 35, 0.6); border-radius: 16px; padding: 20px; text-align: left; border-left: 4px solid var(--accent-color); margin-bottom: 15px; transition: 0.3s; }
        .web-result { border-left-color: #b000ff; }
        .result-card:hover { transform: translateY(-3px); background: rgba(45, 45, 45, 0.8); }
        a { text-decoration: none; color: var(--accent-color); font-weight: 600; font-size: 19px; display: block; margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        p.snippet { color: var(--text-secondary); font-size: 15px; line-height: 1.6; margin: 0; }
    </style>
</head>
<body>
    <h1><span>🕷️</span> Mini-Google</h1>
    <div class="container">
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="Search the real web..." required value="{{ query if query else '' }}">
            <button type="submit">Search</button>
        </form>
        {% if query %}
            <p style="text-align: left; color: #a0a0a0; margin-bottom: 20px;">🚀 Global Results for "<b>{{ query }}</b>" ({{ time }} ms)</p>
            <div class="results">
                {% for res in results %}
                    <div class="result-card {{ 'web-result' if res.type == 'web' else '' }}">
                        <a href="{{ res.link }}" target="_blank">{{ res.title }}</a>
                        <p class="snippet">{{ res.desc }}</p>
                    </div>
                {% endfor %}
                {% if not results %}
                    <p>No results found. (Try again, sometimes the connection times out!)</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower().strip()
    start_time = time.time()
    final_results = []

    if query:
        # 1. Internal DB Search
        if query in inverted_index:
            for url in inverted_index[query]:
                final_results.append({
                    "title": url, "link": url, 
                    "desc": "Source: Internal Index Database", "type": "internal"
                })

        # 2. REAL WEB SEARCH (DuckDuckGo HTML Scraper)
        try:
            # We use the HTML version because it is lighter and easier to scrape
            url = "https://html.duckduckgo.com/html/"
            payload = {'q': query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find results in the HTML
            count = 0
            for result in soup.find_all('div', class_='result'):
                if count >= 5: break  # Limit to 5 results
                
                link_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                
                if link_tag:
                    title = link_tag.get_text()
                    link = link_tag['href']
                    desc = snippet_tag.get_text() if snippet_tag else "No description available."
                    
                    final_results.append({
                        "title": "🌐 " + title,
                        "link": link,
                        "desc": desc,
                        "type": "web"
                    })
                    count += 1
                    
        except Exception as e:
            print(f"Web Search Error: {e}")

    duration = round((time.time() - start_time) * 1000, 2)
    return render_template_string(HTML_TEMPLATE, query=query, results=final_results, time=duration)

if __name__ == '__main__':
    app.run(debug=True)