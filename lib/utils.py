from __future__ import division

from dogpile.cache import make_region
dpc = make_region().configure('dogpile.cache.memory')

import logging
logging.basicConfig(level=logging.DEBUG)
for handler in logging.root.handlers:  # This makes sure we only show pdiff logs, not logs from all the other modules we import
    handler.addFilter(logging.Filter("npcworld"))
logger = logging.getLogger("npcworld")

FPS = 60
FPS = 10

frames_to_secs = lambda frames: frames / FPS
secs_to_frames = lambda secs: secs * FPS

def replace_true(new_val_fn, cmp, seq):
    """new_val is a function that applies the new value. cmp is a function accepting the current value and returning True if it should be replaced."""
    return tuple(new_val_fn(val) if cmp(val) else val for val in seq)

def build_sse_message(event_type, event_id, data):
    msg = "id: %s\nevent: %s\n" % (event_id, event_type)
    for line in data.strip().split("\n"):
        msg += "data: %s\n" % line
    msg += "\n"
    return str(msg)
