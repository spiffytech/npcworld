import collections
from filecache import filecache
from fn import _
import simplejson as json
import time

from dijkstar import find_path

from npcworld.lib import events, utils
from npcworld.lib.attr_update import attr_update

import sys

@events.event("notify_browser")
def notify_browser(old_world, new_world, event_type, payload):
    browser_event = utils.build_sse_message(
        event_type=event_type,
        event_id=time.time(),  # TODO: come up with a globally-unique thing I can put here that's replayable for connection catch-up
        data=json.dumps(payload)
    )
    events.browser_events.put(browser_event)

@events.event("new_dot")
def new_dot(old_world, new_world, new_dot):
    return attr_update(new_world, entities=_ + (new_dot,))

@events.event("movement")
def move_dot(old_world, new_world, dot_id, path, speed):  # TODO: Set travel speed while moving. Or something. Have to handle it, since we pass it to the browser, too.
    assert isinstance(path, collections.Iterable)
    assert len(path[0]) == 2
    #import pdb; pdb.set_trace()
    return attr_update(
        new_world,
        entities = lambda entities: utils.replace_true(
            new_val_fn = lambda dot: attr_update(dot, path=path),
            cmp = lambda dot: dot.id == dot_id,
            seq = entities
        )
    )

def plot_path(*args, **kwargs):
    return find_path(*args, **kwargs)

def dot_ai(worldstate):
    events = []  # TODO: No mutable state. This is just a dummy experimental function, anyway.
    # TODO: Update this such that it /looks/ like it's going in the optimal path. Right now paths generated are obviously suboptimal.
    # Appearances also matter. E.g., 20,20 -> 139,100 starts with an upward diagonal, even though that /looks like/ it's running away from the target
    def cost_func(u, v, e, prev_e):
        grid = worldstate.grid
        cell_type = grid[v[0]][v[1]]
        return sys.maxint if cell_type in ["shallow_water", "deep_water"] else 1

    if worldstate.ticks == 0:  # Second event - move dots
        dots = [
            utils.Dot(
                id = 1,
                color = "red",
                pos = {"x": 10, "y": 10},
                dest = (29, 1),
            ),
            utils.Dot(
                id = 2,
                color = "blue",
                pos = {"x": 20, "y": 20},
                dest = (30, 1),
            )
        ]
        for dot in dots:
            events.append(dict(event_type="new_dot", payload=dict(new_dot=dot)))
            events.append(dict(event_type="notify_browser", payload=dict(event_type="new_dot", payload=dot)))
        utils.logger.debug("AI: creating new dots")
        return events

    if worldstate.ticks == 1:  # Second event - move dots
        graph = worldstate.graph
        path1 = plot_path(graph, (10, 10), (159, 1), cost_func=cost_func)
        path2 = plot_path(graph, (20, 20), (139, 100), cost_func=cost_func)
        for dot in worldstate.entities:
            browser_payload = dict(
                dot_id = dot.id,
                path = path1[0] if dot.id == 1 else path2[0],
                speed = dot.speed
            )
            events.append(dict(event_type="movement", payload=browser_payload))

            event_payload = dict(
                event_type="movement",
                payload=browser_payload
            )
            events.append(dict(event_type="notify_browser", payload=event_payload))
        utils.logger.debug("AI: moving dots")
        return events
    return events
