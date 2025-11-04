from flask import Flask, request, jsonify, render_template
import requests
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# সার্ভার লিস্ট + ক্যাটাগরি
servers = {
    "DHAKA-FLIX-7": {"url": "http://172.16.50.7/DHAKA-FLIX-7/", "category": "Movies"},
    "DHAKA-FLIX-8": {"url": "http://172.16.50.8/DHAKA-FLIX-8/", "category": "Series, Software"},
    "DHAKA-FLIX-9": {"url": "http://172.16.50.9/DHAKA-FLIX-9/", "category": "Series"},
    "DHAKA-FLIX-12": {"url": "http://172.16.50.12/DHAKA-FLIX-12/", "category": "Series"},
    "DHAKA-FLIX-14": {"url": "http://172.16.50.14/DHAKA-FLIX-14/", "category": "Movies, Series"},
}

allowed_extensions = ['.mp3', '.mp4', '.mkv', '.iso', '.zip', '.avi']

def has_allowed_extension(filename):
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def get_icon(ext):
    icons = {
        '.mp4': 'fa fa-file-video-o',
        '.mkv': 'fa fa-file-video-o',
        '.mp3': 'fa fa-music',
        '.zip': 'fa fa-file-archive-o',
        '.iso': 'fa fa-compact-disc',
        '.avi': 'fa fa-film',
    }
    return icons.get(ext, 'fa fa-file-o')

def fetch_results(server_name, server_info, query):
    search_results = []
    base_url = server_info["url"]
    categories = [c.strip() for c in server_info["category"].split(",")]
    
    request_json = {
        "action": "get",
        "search": {
            "href": f"/{server_name}/",
            "pattern": query,
            "ignorecase": True
        }
    }
    try:
        response = requests.post(base_url, json=request_json, timeout=30)
        response_data = response.json()
        for item in response_data.get("search", []):
            href = item.get("href")
            if has_allowed_extension(href):
                if href.startswith(f"/{server_name}"):
                    full_link = base_url.rstrip('/') + href.replace(f"/{server_name}", '', 1)
                else:
                    full_link = base_url.rstrip('/') + href
                ext = '.' + href.split('.')[-1].lower()
                search_results.append({
                    "name": unquote(href.split('/')[-1]),
                    "url": full_link,
                    "ext": ext,
                    "icon": get_icon(ext),
                    "server": server_name,
                    "categories": categories
                })
    except Exception as e:
        print(f"Error fetching data from {base_url}: {e}")
    return search_results

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    all_results = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(fetch_results, name, info, query)
            for name, info in servers.items()
        ]
        for future in futures:
            all_results.extend(future.result())

    # ক্যাটাগরি অনুযায়ী গ্রুপ করা
    grouped = {}
    for item in all_results:
        for cat in item["categories"]:
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(item)

    return render_template('index.html', 
                         grouped_results=grouped, 
                         search_performed=True, 
                         query=query)

@app.route('/')
def index():
    return render_template('index.html', grouped_results={}, search_performed=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
