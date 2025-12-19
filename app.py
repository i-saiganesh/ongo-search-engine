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

# 2. The Final "OnGo" UI (Lifted Position)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnGo | Fast Search</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;700&display=swap" rel="stylesheet">

    <style>
        /* THEME VARIABLES */
        :root {
            /* Default: Dark Theme */
            --bg-body: #0D1B2A;       
            --bg-card: rgba(27, 38, 59, 0.6); 
            --bg-input: rgba(255, 255, 255, 0.08);
            --text-main: #E0E1DD;     
            --text-muted: #AAB3C0;
            --accent-sand: #B3AF8F;   
            --accent-blue: #415A77; 
            --shadow: rgba(0,0,0,0.2);
            --border: rgba(255, 255, 255, 0.05);
            
            --font-main: 'Quicksand', sans-serif;
        }

        /* Light Theme Override */
        [data-theme="light"] {
            --bg-body: #F0F2F5;       
            --bg-card: #FFFFFF; 
            --bg-input: #FFFFFF;
            --text-main: #1B263B;     
            --text-muted: #5C677D;
            --accent-sand: #B3AF8F;
            --accent-blue: #A0AEC0; 
            --shadow: rgba(0,0,0,0.08);
            --border: rgba(0, 0, 0, 0.05);
        }
        
        * { box-sizing: border-box; }

        body { 
            background-color: var(--bg-body);
            color: var(--text-main);
            font-family: var(--font-main);
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            
            /* POSITIONING LOGIC: */
            /* If searching: Align to top. */
            /* If home: Center, but use padding-bottom to push it UP. */
            justify-content: {{ 'flex-start' if query else 'center' }}; 
            
            padding-top: {{ '40px' if query else '0' }};
            
            /* CHANGED: Increased from 10vh to 25vh to lift content higher */
            padding-bottom: {{ '0' if query else '25vh' }};
            
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        /* --- THEME TOGGLE BUTTON --- */
        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.2s;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px var(--shadow);
            z-index: 100;
        }
        .theme-toggle:hover { transform: scale(1.1); }
        .theme-toggle svg { width: 20px; height: 20px; fill: currentColor; }

        /* --- BRANDING: OnGo --- */
        h1 { 
            font-family: var(--font-main);
            font-size: 3.5rem; 
            margin: 0 0 30px 0;
            letter-spacing: -1px;
            text-align: center;
            font-weight: 700; 
        }
        
        .logo-link {
            text-decoration: none;
            color: var(--text-main);
            display: inline-block;
            transition: transform 0.2s;
        }
        .logo-link:hover { transform: scale(1.02); }
        
        .logo-link span { 
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

        /* --- SEARCH BAR --- */
        .search-wrapper {
            background: var(--bg-input);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 6px 15px 6px 6px;
            border-radius: 50px;
            display: flex;
            align-items: center;
            width: 100%;
            max-width: 600px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px var(--shadow);
            position: relative;
        }

        .search-wrapper:focus-within {
            border-color: var(--accent-sand);
            box-shadow: 0 8px 25px var(--shadow);
            transform: translateY(-2px);
        }

        input { 
            background: transparent;
            border: none;
            color: var(--text-main);
            font-size: 1.1rem;
            padding: 14px 15px;
            width: 100%;
            font-family: var(--font-main);
            font-weight: 500;
            outline: none;
        }
        
        .clear-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0 10px;
            display: none; 
            line-height: 1;
        }
        .clear-btn:hover { color: var(--accent-sand); }
        
        input:not(:placeholder-shown) + .clear-btn { display: block; }

        .search-btn { 
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
            margin-left: 5px;
        }

        .search-btn:hover { transform: scale(1.05); filter: brightness(1.1); }

        .stats {
            align-self: flex-start;
            margin: 20px 0 15px 0;
            color: var(--text-muted);
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
            border: 1px solid var(--border);
            transition: transform 0.2s ease, background 0.2s;
            text-align: left;
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden; 
            position: relative;
            box-shadow: 0 2px 5px var(--shadow);
        }

        .web-result { border-top: 4px solid var(--accent-sand); }
        .internal-result { border-top: 4px solid var(--accent-blue); }

        .result-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 20px var(--shadow);
            overflow: visible; 
            z-index: 10;
        }

        a.result-link { 
            font-family: var(--font-main);
            font-weight: 700;
            font-size: 1.15rem;
            color: var(--text-main);
            text-decoration: none;
            margin-bottom: 8px;
            line-height: 1.3;
            white-space: nowrap;      
            overflow: hidden;         
            text-overflow: ellipsis;  
            display: block;
            width: 100%;
        }
        
        a.result-link:hover {
            white-space: normal;      
            word-break: break-all;    
            overflow: visible;        
            color: var(--accent-sand);
            background: var(--bg-body); 
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            position: relative;       
            z-index: 20;
            padding: 2px;
        }

        p.snippet {
            color: var(--text-muted); 
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
    <button class="theme-toggle" onclick="toggleTheme()" title="Switch Theme">
        <svg id="sun-icon" viewBox="0 0 24 24" style="display: none;">
            <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zm0 9c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm0-14c.55 0 1 .45 1 1v2c0 .55-.45 1-1 1s-1-.45-1-1V3c0-.55.45-1 1-1zm0 18c.55 0 1 .45 1 1v2c0 .55-.45 1-1 1s-1-.45-1-1v-2c0-.55.45-1 1-1zm10-9c0 .55-.45 1-1 1h-2c-.55 0-1-.45-1-1s.45-1 1-1h2c.55 0 1 .45 1 1zm-18 0c0 .55-.45 1-1 1H2c-.55 0-1-.45-1-1s.45-1 1-1h2c.55 0 1 .45 1 1zm14.85-6.85l1.41 1.41c.39.39.39 1.02 0 1.41-.39.39-1.02.39-1.41 0l-1.41-1.41c-.39-.39-.39-1.02 0-1.41.39-.39 1.02-.39 1.41 0zm-12.72 12.72l1.41 1.41c.39.39.39 1.02 0 1.41-.39.39-1.02.39-1.41 0l-1.41-1.41c-.39-.39-.39-1.02 0-1.41.39-.39 1.02-.39 1.41 0zm12.72 0l-1.41 1.41c-.39.39-1.02.39-1.41 0-.39-.39-.39-1.02 0-1.41l1.41-1.41c.39-.39 1.02-.39 1.41 0 .39.39.39 1.02 0 1.41zm-12.72-12.72l-1.41 1.41c-.39.39-1.02.39-1.41 0-.39-.39-.39-1.02 0-1.41l1.41-1.41c.39-.39 1.02-.39 1.41 0 .39.39.39 1.02 0 1.41z"/>
        </svg>
        <svg id="moon-icon" viewBox="0 0 24 24">
            <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-3.03 0-5.5-2.47-5.5-5.5 0-1.82.89-3.42 2.26-4.4-.44-.06-.9-.1-1.36-.1z"/>
        </svg>
    </button>

    <div class="container">
        <h1>
            <a href="/" class="logo-link">On<span>Go</span></a>
        </h1>
        
        <form action="/search" method="get" style="width: 100%; display: flex; justify-content: center;">
            <div class="search-wrapper">
                <input type="text" id="searchInput" name="q" placeholder="Search the web..." required value="{{ query if query else '' }}" oninput="toggleClearBtn()">
                <button type="button" class="clear-btn" id="clearBtn" onclick="clearSearch()" title="Clear">×</button>
                <button type="submit" class="search-btn">Search</button>
            </div>
        </form>
        
        {% if query %}
            <p class="stats">Found results for "<b>{{ query }}</b>" ({{ time }} ms)</p>
            
            <div class="results">
                {% for res in results %}
                    <div class="result-card {{ 'web-result' if res.type == 'web' else 'internal-result' }}">
                        <a href="{{ res.link }}" class="result-link" target="_blank" title="{{ res.title }}">{{ res.title }}</a>
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

    <script>
        // 1. Theme Logic
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const sunIcon = document.getElementById('sun-icon');
            const moonIcon = document.getElementById('moon-icon');

            if (currentTheme === 'light') {
                body.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'block';
            } else {
                body.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                sunIcon.style.display = 'block';
                moonIcon.style.display = 'none';
            }
        }

        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.setAttribute('data-theme', 'light');
            document.getElementById('sun-icon').style.display = 'block';
            document.getElementById('moon-icon').style.display = 'none';
        }

        // 2. Clear Button Logic
        function toggleClearBtn() {
            const input = document.getElementById('searchInput');
            const btn = document.getElementById('clearBtn');
            btn.style.display = input.value ? 'block' : 'none';
        }

        function clearSearch() {
            const input = document.getElementById('searchInput');
            input.value = '';
            input.focus();
            toggleClearBtn();
        }

        toggleClearBtn();
    </script>
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