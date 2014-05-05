from npcworld.lib import events

def setup_method():
    events.event.events = {}

def test_event():
    # Also incidentally tests get_handler
    @events.event("handler1")
    def handler1():
        pass
    @events.event("handler2")
    def handler2():
        pass

    assert events.get_handler("handler1") == handler1
    assert events.get_handler("handler2") == handler2

def test_handle_event():
    @events.event("handler")
    def handler(old_val, new_val, event):
        return new_val * event

    handled = events.handle_event(1, 2, dict(event_type="handler", payload=2))
    assert handled == 4

def test_handle_events():
    @events.event("handler")
    def handler1(old_val, new_val, event):
        return new_val * event
    @events.event("handler")
    def handler2(old_val, new_val, event):
        return new_val * event

    handled = events.handle_events(1, (dict(event_type="handler", payload=2), dict(event_type="handler", payload=2)))
    assert handled == 4
