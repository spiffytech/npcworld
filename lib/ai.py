from fn import _
import simplejson as json
import time

from dijkstar import find_path

from npcworld.lib import events, utils
from npcworld.lib.attr_update import attr_update

import sys

@events.event("notify_browser")
def notify_browser(old_world, new_world, event_params):
    browser_event = utils.build_sse_message(
        event_type=event_params["event_type"],
        event_id=time.time(),  # TODO: come up with a globally-unique thing I can put here that's replayable for connection catch-up
        data=json.dumps(event_params["payload"])
    )
    utils.logger.debug("Putting event into browser queue")
    events.browser_events.put(browser_event)
    utils.logger.debug("Queue size: %d", events.browser_events.qsize())
    utils.logger.debug("Queue ID when inserted: %s", id(events.browser_events))
    import threading
    utils.logger.debug("Thread ID notify_browser: %s", threading.current_thread())

@events.event("new_dot")
def new_dot(old_world, new_world, new_dot):  # TODO: Pass a Dot object here instead of a dict
    return attr_update(new_world, dots=_ + (new_dot,))

@events.event("movement")
def move_dot(old_world, new_world, payload):
    print payload
    print new_world.dots
    return attr_update(
        new_world,
        dots = lambda dots: utils.replace_true(
            new_val_fn = lambda dot: dict(dot, path=payload["path"]),
            cmp = lambda dot: dot["dot_id"] == payload["dot_id"],
            seq = dots
        )
    )

def dot_ai(worldstate):
    events = []  # TODO: No mutable state. This is just a dummy experimental function, anyway.
    if worldstate.ticks == 0:  # Second event - move dots
        # TODO: Update this such that it always /looks/ like it's going in the optimal path, even if it actually is
        # E.g., 20,20 -> 139,100 starts with an upward diagonal, even though that /looks like/ it's running away from the target
        def cost_func(u, v, e, prev_e):
            grid = worldstate.grid
            cell_type = grid[v[0]][v[1]]
            return sys.maxint if cell_type in ["shallow_water", "deep_water"] else 1

        graph = worldstate.graph
        path1 = find_path(graph, (10, 10), (159, 1), cost_func=cost_func)
        path2 = find_path(graph, (20, 20), (139, 100), cost_func=cost_func)
        dots = [
            {
                "dot_id": 1,
                "color": "red",
                "x": 10,
                "y": 10,
                "dest": (29, 1),
                "path": path1[0],  # [0] is path, [1] is cost for each traversal, [2] is total cost
                "costs": path1[1]  # [0] is path, [1] is cost for each traversal, [2] is total cost
            }, {
                "dot_id": 2,
                "color": "blue",
                "x": 20,
                "y": 20,
                "dest": (30, 1),
                "path": path2[0],  # [0] is path, [1] is cost for each traversal, [2] is total cost
                "costs": path2[1]  # [0] is path, [1] is cost for each traversal, [2] is total cost
            }
        ]
        for dot in dots:
            events.append(dict(event_type="new_dot", payload=dot))
            events.append(dict(event_type="notify_browser", payload=dict(event_type="new_dot", payload=dot)))
        utils.logger.debug("AI: creating new dots")
        return events

    if worldstate.ticks == 1:  # Second event - move dots
        for dot in worldstate.dots:
            browser_payload = dict(
                dot_id = dot["dot_id"],
                path = dot["path"],
                speed = .1  # sleep time. TODO: Replace this with fixed timestapms instead of sleep durations.
            )
            events.append(dict(event_type="movement", payload=browser_payload))

            event_payload = dict(
                event_type="movement",
                payload=browser_payload
            )
            events.append(dict(event_type="notify_browser", payload=event_payload))
        utils.logger.debug("AI: moving dots")
        return events
