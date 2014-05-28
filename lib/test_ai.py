from npcworld.lib import ai, events, utils
from collections import namedtuple

def test_notify_browser():
    world = namedtuple("World", "")()
    new_world = ai.notify_browser(world, world, dict(event_type="dummy_event", payload=2))
    assert events.browser_events.qsize() == 1

def test_move_dot():
    world = namedtuple("World", "dots")(dots=(utils.Dot(id=1, color=None, pos=dict(x=0,y=0)),))

    new_world = ai.move_dot(world, world, dict(dot_id=1, path=(0, 1)))

    assert new_world.dots[0].path == (0, 1)
