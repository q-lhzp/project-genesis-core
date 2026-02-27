import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class StateManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.state = {}
        self.lock = threading.RLock()
        self._load_initial_state()

    def _load_initial_state(self):
        """Pre-load all JSON files from the data directory into RAM."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                domain = filename.replace(".json", "")
                path = os.path.join(self.data_dir, filename)
                try:
                    with open(path, "r") as f:
                        self.state[domain] = json.load(f)
                    print(f"[STATE] Loaded domain: {domain}", flush=True)
                except Exception as e:
                    print(f"[STATE] Error loading {domain}: {e}")

    def get_domain(self, domain):
        with self.lock:
            return self.state.get(domain, {})

    def update_domain(self, domain, data, merge=True):
        """Update a domain. If merge is True, performs a deep merge."""
        with self.lock:
            if domain not in self.state or not merge:
                self.state[domain] = data
            else:
                # Basic merge (one level deep for now)
                if isinstance(self.state[domain], dict) and isinstance(data, dict):
                    self.state[domain].update(data)
                else:
                    self.state[domain] = data
            
            # Persist to disk (Atomic write)
            self._persist(domain)
            return True

    def _persist(self, domain):
        path = os.path.join(self.data_dir, f"{domain}.json")
        temp_path = path + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(self.state[domain], f, indent=2)
            os.replace(temp_path, path)
        except Exception as e:
            print(f"[STATE] Persist error for {domain}: {e}")

class StateRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        parts = path.strip("/").split("/")
        
        # 1. Static Assets (Dashboard & Plugins)
        if path == "/" or path == "/index.html":
            self._serve_static("dashboard/index.html", "text/html")
            return
        elif path == "/core.js":
            self._serve_static("dashboard/core.js", "application/javascript")
            return
        elif path.startswith("/shared/media/") and len(parts) >= 3:
            # Route: /shared/media/{folder}/{file}
            self._serve_static(path.lstrip("/"))
            return
        elif parts[0] == "plugins" and len(parts) >= 3:
            # Route: /plugins/{id}/frontend/{file}
            plugin_id = parts[1]
            filename = "/".join(parts[2:])
            file_path = os.path.join("kernel/plugins", plugin_id, filename)
            self._serve_static(file_path)
            return

        # 2. State API
        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "state":
            domain = parts[2]
            data = self.server.state_manager.get_domain(domain)
            self._send_json(data)
        elif path == "/v1/plugins":
            manifests = self.server.plugin_manager.get_plugin_manifests() if hasattr(self.server, 'plugin_manager') else []
            self._send_json(manifests)
        elif path == "/v1/health":
            self._send_json({"status": "running", "version": "0.1.0"})

        # 3. Plugin API Routes
        elif len(parts) >= 4 and parts[0] == "v1" and parts[1] == "plugins":
            plugin_id = parts[2]
            route = "/".join(parts[3:]) if len(parts) > 3 else ""
            self._handle_plugin_route(plugin_id, "GET", route)
        else:
            self.send_error(404)

    def _serve_static(self, rel_path, content_type=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, rel_path)
        
        if not os.path.isfile(full_path):
            self.send_error(404)
            return

        if not content_type:
            ext = os.path.splitext(full_path)[1].lower()
            content_type = {
                ".html": "text/html",
                ".js": "application/javascript",
                ".css": "text/css",
                ".png": "image/png",
                ".jpg": "image/jpeg"
            }.get(ext, "application/octet-stream")

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def do_PATCH(self):
        self._handle_write(merge=True)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        parts = parsed_path.path.strip("/").split("/")

        # Check for plugin POST routes
        if len(parts) >= 4 and parts[0] == "v1" and parts[1] == "plugins":
            plugin_id = parts[2]
            route = "/".join(parts[3:]) if len(parts) > 3 else ""
            self._handle_plugin_route(plugin_id, "POST", route)
        else:
            self._handle_write(merge=False)

    def _handle_write(self, merge):
        parsed_path = urlparse(self.path)
        parts = parsed_path.path.strip("/").split("/")
        
        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "state":
            domain = parts[2]
            content_length = int(self.headers.get('Content-Length', 0))
            try:
                body = json.loads(self.rfile.read(content_length).decode('utf-8'))
                if self.server.state_manager.update_domain(domain, body, merge=merge):
                    self._send_json({"success": True, "domain": domain})
                else:
                    self.send_error(500)
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _handle_plugin_route(self, plugin_id, method, route):
        """Handle plugin API routes from manifest."""
        if not hasattr(self.server, 'plugin_manager'):
            self.send_error(500, "No plugin manager")
            return

        plugin = self.server.plugin_manager.get_plugin_by_id(plugin_id)
        if not plugin:
            self.send_error(404, f"Plugin {plugin_id} not found")
            return

        manifest = plugin["manifest"]
        module = plugin["module"]

        if not module:
            self.send_error(500, f"Plugin {plugin_id} has no backend module")
            return

        # Find matching route in manifest
        api_routes = manifest.get("api_routes", {})
        full_route = f"{method} /v1/plugins/{plugin_id}/{route}"

        handler_name = None
        for route_pattern, handler in api_routes.items():
            if route_pattern == full_route or (method in route_pattern and route in route_pattern):
                handler_name = handler
                break

        if not handler_name:
            # Try shorter match
            for route_pattern, handler in api_routes.items():
                if route_pattern.startswith(method) and route_pattern.endswith(route):
                    handler_name = handler
                    break

        if not handler_name:
            self.send_error(404, f"No handler for {full_route}")
            return

        # Call the handler
        try:
            handler = getattr(module, handler_name, None)
            if handler and callable(handler):
                result = handler()
                self._send_json(result)
            else:
                self.send_error(500, f"Handler {handler_name} not callable")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

def run_server(port=5000, data_dir="data"):
    state_manager = StateManager(data_dir)
    server = HTTPServer(("", port), StateRequestHandler)
    server.state_manager = state_manager
    print(f"--- GENESIS CORE KERNEL STARTING ON PORT {port} ---")
    print(f"[CORE] Storage: {os.path.abspath(data_dir)}")
    server.serve_forever()

if __name__ == "__main__":
    import sys
    # Use workspace relative data dir if possible
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data")
    run_server(data_dir=data_path)
