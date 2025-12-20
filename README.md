# OnGo. | High-Performance Internal Search Engine

### 🚀 A pure-Python search engine utilizing Inverted Indices for O(1) lookup speeds.

![Complexity](https://img.shields.io/badge/Time_Complexity-O(1)-success) ![Language](https://img.shields.io/badge/Python-3.10-blue) ![Architecture](https://img.shields.io/badge/Architecture-Inverted_Index-orange) ![Status](https://img.shields.io/badge/Status-Live-green)

## 💡 Overview
**OnGo.** is an engineering-focused search engine built from scratch. Unlike standard "wrapper" applications that rely on external APIs (Google/Bing), OnGo implements a custom **Inverted Index** data structure using Hash Maps to perform instant information retrieval.

It demonstrates core Computer Science fundamentals:
* **Data Structures:** Hash Map (Dictionary) & Lists.
* **Algorithms:** Constant Time O(1) Lookup.
* **System Design:** In-Memory Database (RAM-based storage).

## ⚡ Engineering & Performance
* **Zero Latency:** Queries are resolved in **<0.01ms** (Sub-millisecond) because they access RAM directly.
* **O(1) Complexity:** Search time remains constant regardless of database size, bypassing the need for linear O(N) scans.
* **Privacy-First:** No API keys, no external trackers, and no data leaves the server.
* **Fault Tolerant:** Fallback mechanisms ensure the engine runs even if the index file is missing.

## 🛠️ Technical Stack
* **Backend:** Python 3 (Flask)
* **Data Store:** JSON (Persistent) -> Python Dictionary (In-Memory)
* **Server:** Gunicorn (Production WSGI)
* **Frontend:** HTML5, CSS3 (Quicksand Typography, Dark Mode)

## 🔍 How It Works (The Algorithm)
1.  **Initialization:** On startup, the server reads the `inverted_index.json` database.
2.  **Indexing:** It constructs a **Hash Map** in RAM where:
    * **Key:** The search term (e.g., `"python"`)
    * **Value:** A list of relevant URLs (e.g., `["python.org", "realpython.com"]`)
3.  **Retrieval:** When a user searches, the engine performs a direct key lookup:
    ```python
    # The Core Logic
    results = inverted_index.get(query) # O(1) Operation
    ```

## 🚀 Usage
1.  **Clone the Repo:**
    ```bash
    git clone [https://github.com/i-saiganesh/ongo-search-engine.git](https://github.com/i-saiganesh/ongo-search-engine.git)
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Locally:**
    ```bash
    python app.py
    ```
4.  **Search:** Try keywords like `python`, `dsa`, `algo`, or `ganesh`.

## 🔮 Future Roadmap
* [ ] Implement a **BFS Web Crawler** to auto-populate the index.
* [ ] Add **Trie Data Structure** for prefix-based autocomplete.
* [ ] Implement **TF-IDF** scoring to rank results by relevance.

---
**Built with 💻 by Ganesh**