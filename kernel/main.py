import asyncio
import threading
import os
import sys

# Setup path to include project root before imports that depend on it
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from http.server import HTTPServer
from kernel.core.state_server import StateManager, StateRequestHandler
from kernel.core.event_bus import bus
from kernel.core.clock import clock
from kernel.core.plugin_loader import PluginLoader
from kernel.core.logger import logger

class GenesisKernel:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.plugins_dir = os.path.join(base_dir, "kernel", "plugins")
        
        # 1. Initialize State Manager
        self.state_manager = StateManager(self.data_dir)
        
        # 2. Initialize Event Bus & Clock
        self.event_bus = bus
        self.clock = clock
        
        # 3. Initialize Plugin Loader
        self.plugin_loader = PluginLoader(self, self.plugins_dir)

    def start_api_server(self, port=5000):
        """Starts the REST API server in a separate thread."""
        server = HTTPServer(("", port), StateRequestHandler)
        server.state_manager = self.state_manager
        server.plugin_manager = self.plugin_loader # Allow API to route to plugins

        # Safe logging - check if logger supports data kwarg
        try:
            logger.info(f"GENESIS KERNEL API STARTING ON PORT {port}", data={"port": port})
        except TypeError:
            # Fallback if logger not ready
            print(f"GENESIS KERNEL API STARTING ON PORT {port}")
        api_thread = threading.Thread(target=server.serve_forever, daemon=True)
        api_thread.start()
        return server

    async def run(self):
        """Main asynchronous execution loop."""
        logger.info("PROJECT GENESIS CORE KERNEL STARTING")

        # 1. Discover and load plugins (wrapped in try-except for stability)
        try:
            self.plugin_loader.discover_and_load()
        except Exception as e:
            logger.error(f"Plugin loading failed: {e}")
            # Continue anyway - don't let a single plugin crash the kernel

        # 2. Start API Server
        self.start_api_server()

        # 3. Start Event Processing & Clock
        tasks = [
            asyncio.create_task(self.event_bus.start_processing()),
            asyncio.create_task(self.clock.start())
        ]

        logger.info("KERNEL FULLY OPERATIONAL")
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Setup path to include project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)
    
    kernel = GenesisKernel(project_root)
    
    try:
        asyncio.run(kernel.run())
    except KeyboardInterrupt:
        logger.info("KERNEL SHUTTING DOWN")
