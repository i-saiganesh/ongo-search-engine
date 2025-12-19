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

# 2. The "iOS / Dune" Modern UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini-Google</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=BBH+Bartle&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

    <style>
        :root {
            /* Palette */
            --bg-dark: #0D1B2A;       /* Deep Navy */
            --bg-card: rgba(27, 38, 59, 0.7); /* Glassy Blue */
            --text-main: #E0E1DD;     /* Bone White */
            --accent-sand: #B3AF8F;   /* Gold/Sand */
            --accent-blue: #415A77;   /* Muted Blue */
            
            /* Fonts */
            --font-display: 'BBH Bartle', serif; 
            --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; /* iOS System stack */
        }
        
        * { box-sizing: border-box; }

        body { 
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-body);
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        /* 1. Responsive Heading (Fits properly on any screen) */
        h1 { 
            font-family: var(--font-display);
            /* clamp(min, preferred, max) -> scales smoothly */
            font-size: clamp(3rem, 12vw, 6rem); 
            margin: 0 0 40px 0;
            letter-spacing: -0.03em;
            text-transform: uppercase;
            color: var(--text-main);
            text-align: center;
            line-height: 1;
            width: 100%;
        }
        
        h1 span {
            color: var(--accent-sand);
        }

        .container {
            width: 100%;
            max-width: 700px; /* Optimal reading width */
            text-align: center;
        }

        /* 2. iPhone-style Rounded Search Bar */
        .search-wrapper {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 8px;
            border-radius: 50px; /* Fully rounded pill shape */
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }

        .search-wrapper:focus-within {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--accent-sand);
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            transform: scale(1.01);
        }

        input { 
            background: transparent;
            border: none;
            color: var(--text-main);
            font-size: 1.1rem;
            padding: 12px 20px;
            width: 100%;
            font-family: var(--font-body);
            font-weight: 400;
            outline: none;
        }

        input::placeholder {
            color: var(--accent-blue);
            font-weight: 300;
        }

        /* Round Button */
        button { 
            background-color: var(--accent-sand);
            color: var(--bg-dark);
            border: none;
            border-radius: 40px;
            padding: 12px 30px;
            font-family: var(--font-display);
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: transform 0.2s;
            flex-shrink: 0; /* Prevents button from shrinking on small phones */
        }

        button:hover {
            transform: scale(1.05);
            background-color: #E0E1DD;
        }

        /* 3. iPhone-style Results Cards */
        .stats {
            margin: 20px 0 10px;
            color: var(--accent-blue);
            font-size: 0.85rem;
            text-align: left;
            padding-left: 15px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .results {
            display: flex;
            flex-direction: column;
            gap: 16px;
            text-align: left;
            padding-bottom: 40px;
        }

        .result-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px); /* Glass effect */
            -webkit-backdrop-filter: blur(12px);
            padding: 24px;
            border-radius: 28px; /* High curvature (Apple style) */
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s ease, background 0.2s;
        }
        
        .web-result {
            /* Subtle distinction for web results */
            background: rgba(65, 90, 119, 0.15); 
        }

        .result-card:hover {
            transform: scale(1.02);
            background: rgba(255, 255, 255, 0.08);
        }

        a { 
            font-family: var(--font-display);
            font-size: 1.4rem;
            color: var(--text-main);
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
            line-height: 1.1;
        }
        
        a:hover {
            color: var(--accent-sand);
        }

        p.snippet {
            color: #AAB3C0; 
            line-height: 1.5;
            font-size: 0.95rem;
            font-weight: 300;
            margin: 0;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mini<span>Google</span></h1>
        
        <form action="/search" method="get">
            <div class="search-wrapper">
                <input type="text" name="q" placeholder="Search the web..." required value="{{ query if query else '' }}">
                <button type="submit">Search</button>
            </div>
        </form>
        
        {% if query %}
            <p class="stats">Result for "<b>{{ query }}</b>" ({{ time }} ms)</p>
            
            <div class="results">
                {% for res in results %}
                    <div class="result-card {{ 'web-result' if res.type == 'web' else '' }}">
                        <a href="{{ res.link }}" target="_blank">{{ res.title }}</a>
                        <p class="snippet">{{ res.desc }}</p>
                    </div>
                {% endfor %}
                
                {% if not results %}
                    <div class="result-card">
                        <p class="snippet" style="text-align: center;">No results found. Try a different term.</p>
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

        # 2. Web Search (Scraper)
        try:
            url = "https://html.duckduckgo.com/html/"
            payload = {'q': query}
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0
            for result in soup.find_all('div', class_='result'):
                if count >= 6: break
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