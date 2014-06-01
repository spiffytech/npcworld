from collections import namedtuple
from npcworld.lib import ai, events, utils

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
    def handler(old_val, new_val, payload):
        return new_val * payload

    handled = events.handle_event(1, 2, dict(event_type="handler", payload=dict(payload=2)))
    assert handled == 4

def test_handle_events():
    @events.event("handler")
    def handler1(old_val, new_val, payload):
        return new_val * payload
    @events.event("handler")
    def handler2(old_val, new_val, payload, bonus=0):
        return new_val * payload + bonus

    handled = events.handle_events(1, (
        dict(event_type="handler", payload=dict(payload=2)),
        dict(event_type="handler", payload=dict(payload=3, bonus=3))
    ))
    assert handled == 9  # 1 * 2 * 3 + 3

def test_new_dot_event():
    world = namedtuple("World", "entities")(entities=tuple())
    new_dot = utils.Dot(id=1, color=None, pos=dict(x=0, y=0))
    new_world = ai.new_dot(world, world, new_dot)
    assert new_world.entities[0] == new_dot
