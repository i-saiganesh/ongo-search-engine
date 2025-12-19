from flask import Flask, request, render_template_string
import json
import time
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 1. Load Internal Index
INDEX_FILE = "inverted_index.json"
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# 2. The Final "Smart Grid" UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini-Google</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;700&display=swap" rel="stylesheet">

    <style>
        :root {
            /* Palette */
            --bg-dark: #0D1B2A;       
            --bg-card: rgba(27, 38, 59, 0.6); 
            --text-main: #E0E1DD;     
            --accent-sand: #B3AF8F;   
            --accent-blue: #415A77;   
            
            --font-main: 'Quicksand', sans-serif;
        }
        
        * { box-sizing: border-box; }

        body { 
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-main);
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: {{ 'flex-start' if query else 'center' }}; 
            padding-top: {{ '40px' if query else '0' }};
            transition: all 0.5s ease;
        }

        h1 { 
            font-family: var(--font-main);
            font-size: 3rem; 
            margin: 0 0 30px 0;
            letter-spacing: -1px;
            color: var(--text-main);
            text-align: center;
            font-weight: 300;
        }
        
        h1 span {
            font-weight: 700;
            color: var(--accent-sand);
        }

        .container {
            width: 90%;
            max-width: 1000px; 
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .search-wrapper {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 6px;
            border-radius: 50px;
            display: flex;
            align-items: center;
            width: 100%;
            max-width: 600px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .search-wrapper:focus-within {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--accent-sand);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            transform: translateY(-2px);
        }

        input { 
            background: transparent;
            border: none;
            color: var(--text-main);
            font-size: 1.1rem;
            padding: 14px 25px;
            width: 100%;
            font-family: var(--font-main);
            font-weight: 500;
            outline: none;
        }

        button { 
            background-color: var(--accent-sand);
            color: var(--bg-dark);
            border: none;
            border-radius: 40px;
            padding: 12px 28px;
            font-family: var(--font-main);
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            margin-right: 4px;
        }

        button:hover {
            transform: scale(1.05);
            background-color: #E0E1DD;
        }

        .stats {
            align-self: flex-start;
            margin: 20px 0 15px 0;
            color: var(--accent-blue);
            font-size: 0.9rem;
            font-weight: 500;
            width: 100%;
            max-width: 1000px;
        }

        .results {
            width: 100%;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            padding-bottom: 50px;
        }

        .result-card {
            background: var(--bg-card);
            padding: 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s ease, background 0.2s;
            text-align: left;
            display: flex;
            flex-direction: column;
            height: 100%;
            
            /* CRITICAL FIX: Prevent overlap */
            overflow: hidden; 
            position: relative;
        }

        .web-result { border-top: 4px solid var(--accent-sand); }
        .internal-result { border-top: 4px solid var(--accent-blue); }

        .result-card:hover {
            transform: translateY(-4px);
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            /* Allow content to flow out if needed on hover, though usually not needed with the wrap fix */
            overflow: visible; 
            z-index: 10;
        }

        /* --- THE LINK FIX --- */
        a { 
            font-family: var(--font-main);
            font-weight: 700;
            font-size: 1.15rem;
            color: var(--text-main);
            text-decoration: none;
            margin-bottom: 8px;
            line-height: 1.3;
            
            /* 1. Default: Truncate with Ellipsis */
            white-space: nowrap;      /* Force one line */
            overflow: hidden;         /* Hide spillover */
            text-overflow: ellipsis;  /* Add '...' */
            display: block;
            width: 100%;
        }
        
        /* 2. Hover: Show Full Text */
        a:hover {
            white-space: normal;      /* Allow wrapping */
            word-break: break-all;    /* Force break if it's a super long URL with no spaces */
            overflow: visible;        /* Show everything */
            color: var(--accent-sand);
            background: rgba(13, 27, 42, 0.9); /* Dark background to make it readable over other items */
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            position: relative;       /* Pop out */
            z-index: 20;
        }

        p.snippet {
            color: #AAB3C0; 
            line-height: 1.5;
            font-size: 0.9rem;
            font-weight: 400;
            margin: 0;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mini<span>Google</span></h1>
        
        <form action="/search" method="get" style="width: 100%; display: flex; justify-content: center;">
            <div class="search-wrapper">
                <input type="text" name="q" placeholder="Search the web..." required value="{{ query if query else '' }}">
                <button type="submit">Search</button>
            </div>
        </form>
        
        {% if query %}
            <p class="stats">Found results for "<b>{{ query }}</b>" ({{ time }} ms)</p>
            
            <div class="results">
                {% for res in results %}
                    <div class="result-card {{ 'web-result' if res.type == 'web' else 'internal-result' }}">
                        <a href="{{ res.link }}" target="_blank" title="{{ res.title }}">{{ res.title }}</a>
                        <p class="snippet">{{ res.desc }}</p>
                    </div>
                {% endfor %}
                
                {% if not results %}
                    <div class="result-card" style="grid-column: 1 / -1; text-align: center;">
                        <p class="snippet">No results found. Try a different term.</p>
                    </div>
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
        # 1. Internal DB
        if query in inverted_index:
            for url in inverted_index[query]:
                final_results.append({
                    "title": url, "link": url, 
                    "desc": ":: Internal Database Match", "type": "internal"
                })

        # 2. Web Search
        try:
            url = "https://html.duckduckgo.com/html/"
            payload = {'q': query}
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0
            for result in soup.find_all('div', class_='result'):
                if count >= 9: break 
                link_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                if link_tag:
                    final_results.append({
                        "title": link_tag.get_text(),
                        "link": link_tag['href'],
                        "desc": snippet_tag.get_text() if snippet_tag else "Click to read more...",
                        "type": "web"
                    })
                    count += 1
        except Exception as e:
            print(f"Error: {e}")

    duration = round((time.time() - start_time) * 1000, 2)
    return render_template_string(HTML_TEMPLATE, query=query, results=final_results, time=duration)

if __name__ == '__main__':
    app.run(debug=True)