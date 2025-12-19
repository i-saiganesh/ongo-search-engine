from flask import Flask, request, render_template_string
import json
import time
import os
from duckduckgo_search import DDGS  # The tool for Real Search

app = Flask(__name__)

# 1. Load the Internal Index (Fast Local Results)
INDEX_FILE = "inverted_index.json"
print("🚀 Loading Index...")
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# 2. The "Stealth Mode" Dark UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini-Google | Stealth</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        :root {
            --bg-color: #0a0a0a;
            --card-bg: rgba(25, 25, 25, 0.85);
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent-color: #00f2ff;
            --accent-gradient: linear-gradient(135deg, #00c6ff, #0072ff);
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 20% 30%, rgba(0, 242, 255, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(188, 19, 254, 0.05) 0%, transparent 50%);
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            color: var(--text-primary);
            overflow-x: hidden;
        }

        h1 { 
            font-weight: 800;
            font-size: 3.5rem; 
            margin-top: 60px; 
            letter-spacing: -1px;
            background: linear-gradient(to right, #fff, #a0a0a0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        
        h1 span { color: var(--accent-color); -webkit-text-fill-color: var(--accent-color); }

        .container {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 50px;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            width: 85%;
            max-width: 650px;
            text-align: center;
            animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        form { display: flex; gap: 10px; justify-content: center; margin-bottom: 30px; }

        input { 
            padding: 18px 25px; 
            width: 65%; 
            border-radius: 14px; 
            border: 2px solid rgba(255, 255, 255, 0.1);
            background: rgba(0,0,0,0.3);
            color: var(--text-primary);
            font-size: 17px;
            font-family: inherit;
            outline: none;
            transition: all 0.3s ease;
        }
        input::placeholder { color: rgba(255, 255, 255, 0.4); }

        input:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
            background: rgba(0,0,0,0.5);
        }

        button { 
            padding: 18px 35px; 
            background: var(--accent-gradient);
            color: white; 
            border: none; 
            border-radius: 14px; 
            font-size: 17px;
            font-weight: 700;
            font-family: inherit;
            cursor: pointer; 
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
        }

        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 114, 255, 0.5);
        }

        .stats { 
            color: var(--text-secondary); 
            font-size: 15px; 
            margin-bottom: 25px; 
            text-align: left;
            font-weight: 500;
        }
        .stats b { color: var(--accent-color); }

        .results { display: flex; flex-direction: column; gap: 15px; }

        .result-card {
            background: rgba(35, 35, 35, 0.6);
            border-radius: 16px;
            padding: 20px;
            text-align: left;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-left: 4px solid var(--accent-color);
            transition: all 0.3s ease;
        }

        /* Distinct Style for Real Web Results */
        .web-result {
            border-left-color: #b000ff; /* Purple for Web Results */
        }

        .result-card:hover {
            transform: translateY(-3px) scale(1.01);
            background: rgba(45, 45, 45, 0.8);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        a { 
            text-decoration: none; 
            color: var(--accent-color); 
            font-weight: 600; 
            font-size: 19px; 
            display: block; 
            margin-bottom: 8px;
            transition: color 0.2s;
        }
        a:hover { color: #fff; text-decoration: underline; }
        
        p.snippet { 
            color: var(--text-secondary); 
            font-size: 15px; 
            line-height: 1.6; 
            margin: 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
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
            <p class="stats">🚀 Found results for "<b>{{ query }}</b>" in {{ time }} ms</p>
            
            <div class="results">
                {% for url in db_results %}
                    <div class="result-card">
                        <a href="{{ url }}" target="_blank">{{ url }}</a>
                        <p class="snippet">Source: Internal Index Database (Fast Match)</p>
                    </div>
                {% endfor %}

                {% for res in web_results %}
                    <div class="result-card web-result">
                        <a href="{{ res.href }}" target="_blank">🌐 {{ res.title }}</a>
                        <p class="snippet">{{ res.body }}</p>
                    </div>
                {% endfor %}

                {% if not db_results and not web_results %}
                    <p class="no-results">No results found. The internet seems quiet today.</p>
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
    
    db_results = []
    web_results = []
    duration = 0

    if query:
        # 1. Search Local Database
        db_results = inverted_index.get(query, [])
        
        # 2. Search Real Web (DuckDuckGo)
        # We fetch top 5 results if local DB has fewer than 2 results
        if len(db_results) < 2:
            try:
                with DDGS() as ddgs:
                    # Fetch 5 web results
                    results = list(ddgs.text(query, max_results=5))
                    web_results = results
            except Exception as e:
                print(f"Search Error: {e}")

        duration = round((time.time() - start_time) * 1000, 2)
    
    return render_template_string(
        HTML_TEMPLATE, 
        query=query, 
        db_results=db_results, 
        web_results=web_results,
        time=duration
    )

if __name__ == '__main__':
    app.run(debug=True)