import asyncio
import json
import logging
from typing import Dict, List, Callable, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='[EVENT_BUS] %(message)s')
logger = logging.getLogger("event_bus")

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.queue = asyncio.Queue()
        self._running = True

    def subscribe(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info(f"New subscription for: {event_type}")

    async def publish(self, event_type: str, source: str, data: Any):
        """Put an event into the processing queue."""
        event = {
            "event": event_type,
            "source": source,
            "data": data
        }
        await self.queue.put(event)

    async def start_processing(self):
        """Process events from the queue and notify subscribers."""
        logger.info("Event processing loop started.")
        while self._running:
            try:
                event = await self.queue.get()
                event_type = event["event"]
                
                # Notify specific subscribers
                if event_type in self.subscribers:
                    for callback in self.subscribers[event_type]:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                
                # Notify wildcard subscribers (if any)
                if "*" in self.subscribers:
                    for callback in self.subscribers["*"]:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                            
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event: {e}")
            await asyncio.sleep(0.01)

    def stop(self):
        self._running = False

# Singleton instance for the Kernel
bus = EventBus()
