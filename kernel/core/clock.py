import asyncio
import time
from datetime import datetime
from kernel.core.event_bus import bus

class GenesisClock:
    def __init__(self, interval_seconds=60):
        self.interval = interval_seconds
        self.running = True

    async def start(self):
        """Standard clock loop emitting ticks."""
        print(f"[CLOCK] Started with {self.interval}s interval.")
        while self.running:
            now = datetime.now()
            
            # Emit minutely tick
            await bus.publish("TICK_MINUTELY", "kernel.clock", {
                "timestamp": now.isoformat(),
                "hour": now.hour,
                "minute": now.minute
            })
            
            # Emit hourly tick if applicable
            if now.minute == 0:
                await bus.publish("TICK_HOURLY", "kernel.clock", {
                    "timestamp": now.isoformat(),
                    "hour": now.hour
                })

            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False

# Instance for the Kernel
clock = GenesisClock()
