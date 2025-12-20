from flask import Flask, request, render_template_string
import json
import os
import time

app = Flask(__name__)

# --- ENGINEERING PART: THE INVERTED INDEX ---
# Complexity: O(1) Average Case for Lookups
# Data Structure: Hash Map (Python Dictionary)
INDEX_FILE = "inverted_index.json"
inverted_index = {}

def load_index():
    global inverted_index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            inverted_index = json.load(f)
        print(f"✅ [SYSTEM] Index loaded into RAM: {len(inverted_index)} keys.")
    else:
        print("⚠️ [SYSTEM] Index file missing.")

# Load data immediately on startup
load_index()

# --- UI PART: FRONTEND ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnGo. | DSA Search Engine</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg-body: #0D1B2A; --bg-card: rgba(27, 38, 59, 0.6); --text-main: #E0E1DD; --text-muted: #AAB3C0; --accent: #B3AF8F; --border: rgba(255, 255, 255, 0.05); --font: 'Quicksand', sans-serif; }
        * { box-sizing: border-box; }
        body { background-color: var(--bg-body); color: var(--text-main); font-family: var(--font); margin: 0; display: flex; flex-direction: column; align-items: center; padding-top: 60px; min-height: 100vh; }
        h1 { font-size: 3.5rem; margin: 0 0 30px 0; font-weight: 700; }
        .logo-link { text-decoration: none; color: var(--text-main); }
        .logo-link span { color: var(--accent); }
        .container { width: 90%; max-width: 700px; }
        .search-wrapper { background: rgba(255, 255, 255, 0.08); padding: 10px 20px; border-radius: 50px; display: flex; align-items: center; border: 1px solid var(--border); margin-bottom: 30px; }
        input { background: transparent; border: none; color: var(--text-main); font-size: 1.1rem; width: 100%; font-family: var(--font); outline: none; }
        .search-btn { background-color: var(--accent); color: #0D1B2A; border: none; border-radius: 40px; padding: 10px 25px; font-weight: 700; cursor: pointer; }
        .stats { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
        .card { background: var(--bg-card); padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid var(--border); transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); border-color: var(--accent); }
        .card a { color: var(--text-main); font-weight: 700; text-decoration: none; font-size: 1.2rem; display: block; margin-bottom: 5px; }
        .tag { font-family: monospace; font-size: 0.75rem; color: var(--accent); background: rgba(179, 175, 143, 0.15); padding: 3px 6px; border-radius: 4px; }
        .empty { text-align: center; color: var(--text-muted); margin-top: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center;"><a href="/" class="logo-link">On<span>Go.</span></a></h1>
        <form action="/search" method="get">
            <div class="search-wrapper">
                <input type="text" name="q" placeholder="Search index (e.g., python, dsa)..." value="{{ query }}" autocomplete="off">
                <button type="submit" class="search-btn">Search</button>
            </div>
        </form>

        {% if query %}
            <div class="stats">
                Found {{ results|length }} result(s) in {{ time }}ms (O(1) Lookup)
            </div>
            
            {% for url in results %}
                <div class="card">
                    <a href="{{ url }}" target="_blank">{{ url }}</a>
                    <span class="tag">INDEXED</span>
                </div>
            {% endfor %}

            {% if not results %}
                <div class="empty">
                    <p>No matches in Hash Map for "<b>{{ query }}</b>"</p>
                </div>
            {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, query="", results=[])

@app.route('/search')
def search():
    query = request.args.get('q', '').lower().strip()
    start_time = time.time()
    
    # --- DSA: O(1) LOOKUP ---
    # The heart of the engine. Instant retrieval.
    results = inverted_index.get(query, [])
    
    # Measure speed (Microseconds)
    duration = round((time.time() - start_time) * 1000, 4)
    
    return render_template_string(HTML_TEMPLATE, query=query, results=results, time=duration)

if __name__ == '__main__':
    app.run(debug=True)