import functools
from npcworld.lib.utils import logger

def event(e):
    def _predicate(f):
        @functools.wraps(f)
        def func(*args, **kwargs):
            return f(*args, **kwargs)

        if not hasattr(event, "events"):
            event.events = {}
        event.events[e] = func
        logger.debug("event %s: %s", e, f)

        return func
    return _predicate

def get_handler(event_name):
    return event.events[event_name]

def handle_event(old_world, new_world, event):
    handler = get_handler(event["event_type"])
    return handler(old_world, new_world, event["payload"])

def handle_events(worldstate, events):
    return reduce(  # Using this closure against worldstate instead of just passing tuple of (old_world, new_world) to reduce() to enforce that a handler can't change old_world
        lambda new_world, event: handle_event(worldstate, new_world, event) or new_world,  # Not all handlers will return anything. Some just need to listen and do something else (e.g., notify the browser subsystem)
        events,
        worldstate
    )

