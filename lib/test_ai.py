from npcworld.lib import ai
from collections import namedtuple

def test_notify_browser():
    world = namedtuple("World", "browser")(browser=tuple())
    new_world = ai.notify_browser(world, world, dict(event_type="dummy_event", payload=2))
    assert len(new_world.browser) == 1

def test_new_dot():
    world = namedtuple("World", "dots")(dots=tuple())

    new_dot = dict(dot_id=1)
    new_world = ai.new_dot(world, world, new_dot)
    assert new_world.dots[0] == new_dot

def test_move_dot():
    world = namedtuple("World", "dots")(dots=(dict(dot_id=1),))

    new_world = ai.move_dot(world, world, dict(dot_id=1, path=(0, 1)))

    assert new_world.dots[0]["path"] == (0, 1)
