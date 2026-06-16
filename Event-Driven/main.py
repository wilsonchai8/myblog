import threading
import time

from event_bus import publish_event, consume_event
from agent import EventDrivenAgent

agent = EventDrivenAgent()

def event_loop():
    while True:
        event = consume_event()
        agent.handle_event(event)

threading.Thread(
    target=event_loop,
    daemon=True
).start()

# 模拟 Prometheus 告警
event = {
    "alert_name": "HighErrorRate",
    "service": "order-service"
}

publish_event(event)

time.sleep(30)
