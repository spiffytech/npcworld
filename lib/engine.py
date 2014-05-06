from collections import namedtuple
from Queue import Queue
from fn import recur
import time

from npcworld.lib.utils import logger
from npcworld.lib import ai, utils

browser_events = Queue()

def next_tick_time(current_tick, current_time=None):
    if current_time is None:
        t = time.time()
    else:
        t = current_time
    next_tick = max(t, current_tick + utils.frames_to_secs(1))
    delta = max(0, next_tick - t)  # Time delta to next tick. If we take < 1 frame's time to render a frame, sleep until the next frame tick. If we're taking longer than 1 frame's time to render each frame, don't sleep. 
    if delta == 0:
        logger.warn("Frame ran too long by %d secs", t - next_tick)

    return (
        next_tick,
        delta
    )
