from fn import _
import simplejson as json
import time

from npcworld.lib import events, utils
from npcworld.lib.attr_update import attr_update

@events.event("notify_browser")
def notify_browser(old_world, new_world, event_params):
    new_event = utils.build_sse_message(
        event_type=event_params["event_type"],
        event_id=time.time(),  # TODO: come up with a globally-unique thing I can put here that's replayable for connection catch-up
        data=json.dumps(event_params["payload"])
    )
    return attr_update(new_world, browser = _ + (new_event,))

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
