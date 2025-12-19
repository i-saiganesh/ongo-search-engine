from flask import Flask, request, jsonify, render_template_string
import json
import time
import os

app = Flask(__name__)

# Load the index into memory ONCE when the app starts
INDEX_FILE = "inverted_index.json"
print("🚀 Loading Index...")
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# Simple HTML Interface (Frontend)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini-Google</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        input { padding: 10px; width: 300px; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px 20px; background-color: #4285F4; color: white; border: none; border-radius: 5px; cursor: pointer; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
        a { text-decoration: none; color: #1a0dab; font-size: 18px; }
        .stats { color: #70757a; font-size: 14px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🕷️ Mini-Google</h1>
    <form action="/search" method="get">
        <input type="text" name="q" placeholder="Search the web..." required>
        <button type="submit">Search</button>
    </form>
    {% if query %}
        <p class="stats">Found {{ count }} results in {{ time }} ms</p>
        <ul>
            {% for url in results %}
                <li><a href="{{ url }}" target="_blank">{{ url }}</a></li>
            {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return render_template_string(HTML_TEMPLATE)
    
    start_time = time.time()
    results = inverted_index.get(query, [])
    duration = round((time.time() - start_time) * 1000, 4)
    
    return render_template_string(HTML_TEMPLATE, query=query, results=results, count=len(results), time=duration)

if __name__ == '__main__':
    app.run(debug=True)