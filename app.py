from flask import Flask, request, render_template_string
import json
import time
import os
import requests
from bs4 import BeautifulSoup
import traceback

app = Flask(__name__)

# 1. Load Internal Index
INDEX_FILE = "inverted_index.json"
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# 2. UI Template (Updated 'source' to 'src' to avoid conflict)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnGo | Fast Search</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg-body: #0D1B2A; --bg-card: rgba(27, 38, 59, 0.6); --bg-input: rgba(255, 255, 255, 0.08); --text-main: #E0E1DD; --text-muted: #AAB3C0; --accent-sand: #B3AF8F; --accent-blue: #415A77; --border: rgba(255, 255, 255, 0.05); --font-main: 'Quicksand', sans-serif; }
        [data-theme="light"] { --bg-body: #F0F2F5; --bg-card: #FFFFFF; --bg-input: #FFFFFF; --text-main: #1B263B; --text-muted: #5C677D; --accent-sand: #B3AF8F; --accent-blue: #A0AEC0; --border: rgba(0, 0, 0, 0.05); }
        * { box-sizing: border-box; }
        body { background-color: var(--bg-body); color: var(--text-main); font-family: var(--font-main); min-height: 100vh; margin: 0; display: flex; flex-direction: column; align-items: center; justify-content: {{ 'flex-start' if query else 'center' }}; padding-top: {{ '40px' if query else '0' }}; padding-bottom: {{ '0' if query else '25vh' }}; transition: background-color 0.3s ease, color 0.3s ease; }
        .theme-toggle { position: absolute; top: 20px; right: 20px; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-main); padding: 10px; border-radius: 50%; cursor: pointer; width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; z-index: 100; }
        h1 { font-family: var(--font-main); font-size: 3.5rem; margin: 0 0 30px 0; letter-spacing: -1px; text-align: center; font-weight: 700; }
        .logo-link { text-decoration: none; color: var(--text-main); }
        .logo-link span { font-weight: 700; color: var(--accent-sand); }
        .container { width: 90%; max-width: 1000px; display: flex; flex-direction: column; align-items: center; }
        .search-wrapper { background: var(--bg-input); padding: 6px 15px 6px 6px; border-radius: 50px; display: flex; align-items: center; width: 100%; max-width: 600px; border: 1px solid var(--border); position: relative; }
        input { background: transparent; border: none; color: var(--text-main); font-size: 1.1rem; padding: 14px 15px; width: 100%; font-family: var(--font-main); font-weight: 500; outline: none; }
        .search-btn { background-color: var(--accent-sand); color: var(--bg-dark); border: none; border-radius: 40px; padding: 12px 28px; font-family: var(--font-main); font-weight: 700; font-size: 1rem; cursor: pointer; margin-left: 5px; }
        .stats { align-self: flex-start; margin: 20px 0 15px 0; color: var(--text-muted); font-size: 0.9rem; font-weight: 500; width: 100%; max-width: 1000px; }
        .results { width: 100%; display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; padding-bottom: 50px; }
        .result-card { background: var(--bg-card); padding: 20px; border-radius: 16px; border: 1px solid var(--border); transition: transform 0.2s ease; text-align: left; display: flex; flex-direction: column; height: 100%; overflow: hidden; position: relative; }
        .result-card:hover { transform: translateY(-4px); overflow: visible; z-index: 10; }
        .web-result { border-top: 4px solid var(--accent-sand); }
        .internal-result { border-top: 4px solid var(--accent-blue); }
        .wiki-result { border-top: 4px solid #fff; }
        a.result-link { font-family: var(--font-main); font-weight: 700; font-size: 1.15rem; color: var(--text-main); text-decoration: none; margin-bottom: 8px; line-height: 1.3; display: block; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        a.result-link:hover { white-space: normal; word-break: break-all; overflow: visible; color: var(--accent-sand); background: var(--bg-body); z-index: 20; position: relative; }
        p.snippet { color: var(--text-muted); line-height: 1.5; font-size: 0.9rem; margin: 0; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
        .clear-btn { background: transparent; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; padding: 0 10px; display: none; line-height: 1; }
        input:not(:placeholder-shown) + .clear-btn { display: block; }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌗</button>
    <div class="container">
        <h1><a href="/" class="logo-link">On<span>Go</span></a></h1>
        <form action="/search" method="get" style="width: 100%; display: flex; justify-content: center;">
            <div class="search-wrapper">
                <input type="text" id="searchInput" name="q" placeholder="Search the web..." required value="{{ query if query else '' }}" oninput="toggleClearBtn()">
                <button type="button" class="clear-btn" id="clearBtn" onclick="clearSearch()">×</button>
                <button type="submit" class="search-btn">Search</button>
            </div>
        </form>
        {% if query %}
            <p class="stats">Found results for "<b>{{ query }}</b>" ({{ time }} ms) via {{ src }}</p>
            <div class="results">
                {% for res in results %}
                    <div class="result-card {{ 'web-result' if res.type == 'web' else ('wiki-result' if res.type == 'wiki' else 'internal-result') }}">
                        <a href="{{ res.link }}" class="result-link" target="_blank">{{ res.title }}</a>
                        <p class="snippet">{{ res.desc }}</p>
                    </div>
                {% endfor %}
                {% if not results %}
                    <div class="result-card" style="grid-column: 1 / -1; text-align: center;"><p class="snippet">No results found.</p></div>
                {% endif %}
            </div>
        {% endif %}
    </div>
    <script>
        function toggleTheme() {
            const body = document.body;
            body.setAttribute('data-theme', body.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
            localStorage.setItem('theme', body.getAttribute('data-theme'));
        }
        if (localStorage.getItem('theme') === 'light') document.body.setAttribute('data-theme', 'light');
        function toggleClearBtn() { document.getElementById('clearBtn').style.display = document.getElementById('searchInput').value ? 'block' : 'none'; }
        function clearSearch() { document.getElementById('searchInput').value = ''; toggleClearBtn(); }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    try:
        query = request.args.get('q', '').lower().strip()
        start_time = time.time()
        final_results = []
        # Logic variable stays 'source'
        source = "Internal DB"
        web_results = []

        if query:
            # 1. Internal DB
            if query in inverted_index:
                for url in inverted_index[query]:
                    final_results.append({
                        "title": url, "link": url, 
                        "desc": ":: Internal Database Match", "type": "internal"
                    })

            # 2. Web Search (Primary: DuckDuckGo)
            try:
                url = "https://html.duckduckgo.com/html/"
                payload = {'q': query}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
                }
                response = requests.post(url, data=payload, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    found_items = soup.find_all('div', class_='result')
                    
                    if found_items:
                        count = 0
                        for result in found_items:
                            if count >= 9: break 
                            link_tag = result.find('a', class_='result__a')
                            snippet_tag = result.find('a', class_='result__snippet')
                            if link_tag:
                                web_results.append({
                                    "title": link_tag.get_text(),
                                    "link": link_tag['href'],
                                    "desc": snippet_tag.get_text() if snippet_tag else "Click to read more...",
                                    "type": "web"
                                })
                                count += 1
                        source = "Live Web"
            except Exception as e:
                print(f"DDG Error: {e}")

            # 3. FALBACK: Wikipedia
            if not web_results:
                try:
                    wiki_url = "https://en.wikipedia.org/w/api.php"
                    params = {
                        "action": "opensearch",
                        "search": query,
                        "limit": 9,
                        "namespace": 0,
                        "format": "json"
                    }
                    wiki_resp = requests.get(wiki_url, params=params, timeout=5).json()
                    
                    if len(wiki_resp) == 4 and wiki_resp[1]:
                        titles = wiki_resp[1]
                        descs = wiki_resp[2]
                        links = wiki_resp[3]
                        for i in range(len(titles)):
                            final_results.append({
                                "title": titles[i],
                                "link": links[i],
                                "desc": descs[i] if descs[i] else "Read full article on Wikipedia...",
                                "type": "wiki"
                            })
                        source = "Wikipedia (Backup)"
                except Exception as e:
                    print(f"Wiki Error: {e}")
            else:
                final_results.extend(web_results)

        duration = round((time.time() - start_time) * 1000, 2)
        
        # --- THE FIX IS HERE ---
        # Changed 'source=source' to 'src=source' to prevent argument collision
        return render_template_string(HTML_TEMPLATE, query=query, results=final_results, time=duration, src=source)

    except Exception as e:
        error_msg = traceback.format_exc()
        return f"<h1>CRITICAL ERROR:</h1><pre>{error_msg}</pre>"

if __name__ == '__main__':
    app.run(debug=True)