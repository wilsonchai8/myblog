import queue

event_queue = queue.Queue()

def publish_event(event):
    event_queue.put(event)

def consume_event():
    return event_queue.get()
