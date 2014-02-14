from __future__ import division
from collections import namedtuple
from functools import partial
import random
from fn import _, Stream
from fn.iters import *

def pseudo_normal():
    return (Math.random()*2-1)+(Math.random()*2-1)+(Math.random()*2-1);

def rand_from_normal():
    return Math.round(rnd_snd()*stdev+mean);

# Look at ways to set default values on namedtuples from http://stackoverflow.com/questions/11351032/named-tuple-and-optional-keyword-arguments

Market = namedtuple("Market", ["bid", "ask"])
Inventory = namedtuple("Inventory", ["wood", "food", "ore", "metal", "tools", "dollars"])
Inventory.__new__ = partial(Inventory.__new__, wood=10, food=10, ore=10, metal=10, tools=10, dollars=0)

ResourceDelta = namedtuple("ResourceDelta", ["wood", "food", "ore", "metal", "tools", "dollars"])
ResourceDelta.__new__ = partial(ResourceDelta.__new__, wood=0, food=0, ore=0, metal=0, tools=0, dollars=0)

#Bid = namedtuple("Bid", ["npc", "resource", "price"])
#Ask = namedtuple("Ask", ["npc", "resource", "price"])
Trade = namedtuple("Trade", ["resource", "price", "type", "status"])
Trade.__new__ = partial(Trade.__new__, status=None)

def has_wood(obj):
    return obj.wood > 0
def has_food(obj):
    return obj.food > 0
def has_ore(obj):
    return obj.ore > 0
def has_metal(obj):
    return obj.metal > 0
def has_tools(obj):
    return obj.tools > 0

BeliefIntervals = namedtuple("BeliefIntervals", ["wood", "food", "ore", "metal", "tools"])
BeliefIntervals.__new__ = partial(BeliefIntervals.__new__, wood=0, food=0, ore=0, metal=0, tools=0)

NPC = namedtuple("NPC", ["occupation", "inventory", "belief_intervals"])
NPC.__new__ = partial(
    NPC.__new__,
    occupation=None,
    inventory=Inventory(),
    belief_intervals=BeliefIntervals(),
)

trade_history = ()

def miner_produce(npc):
    inventory = npc.inventory
    print inventory
    if has_food(inventory): 
        if has_tools(inventory):
            delta = dict(food=inventory.food-1, ore=inventory.ore+4)
        else:
            delta = dict(food=inventory.food-1, ore=inventory.ore+2)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)
        
def farmer_produce(npc):
    inventory = npc.inventory
    if has_wood(inventory): 
        if has_tools(inventory):
            delta = dict(wood=inventory.wood-1, food=inventory.food+4)
        else:
            delta = dict(wood=inventory.wood-1, food=inventory.food+2)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)

def lumberjack_produce(npc):
    inventory = npc.inventory
    if has_food(inventory): 
        if has_tools(inventory):
            delta = dict(food=inventory.food-1, wood=inventory.wood+2)
        else:
            delta = dict(food=inventory.food-1, wood=inventory.wood+1)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)

def refiner_produce(npc):
    inventory = npc.inventory
    if has_food(inventory):
        if has_tools(inventory):
            delta = dict(ore=0, food=inventory.food-1, metal=inventory.metal+1)
        elif inventory.ore >= 2:
            delta = dict(ore=inventory.ore-2, food=inventory.food-1, metal=inventory.metal+1)
        else:
            delta = dict()
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)


def get_work_fn(npc):
    occupation_work = dict(
        farmer=farmer_produce,
        lumberjack=lumberjack_produce,
        miner=miner_produce,
        refiner=refiner_produce,
    )
    return occupation_work[npc.occupation]

def do_work(npc):
    return get_work_fn(npc)(npc)

def avg_price(resource, trade_history):
    '''Histories are lists of Trade items'''
    if len(trade_history) == 0:
        raise RuntimeError("Need trades to estimate the history of")

    these_trades = (h for h in trade_history if h.resource == resource)
    n = 8
    to_inspect = tuple(takelast(n, these_trades))
    return sum(map(_.price, to_inspect))/len(to_inspect)

def estimate_market_price(resource):
    return avg_price(trade_history, resource)

def estimate_npc_price(resource, intervals):
    interval = getattr(intervals, resource)
    return random.randint(interval[0], interval[1])

def translate_interval(interval, mean):
    """Translates an interval towards the mean"""
    midpoint = (interval[1] + interval[0])/2
    increment = (mean - midpoint) * .05
    interval = (interval[0]+increment, interval[1]+increment)
    return interval

def shrink_interval(interval):
    return (interval[0]+(interval[0]*.05), interval[1]-(interval[1]*.05))

def expand_interval(interval):
    return (interval[0]-(interval[0]*.05), interval[1]+(interval[1]*.05))

def update_beliefs(npc, trade):
    fn = update_beliefs_accepted if trade.status == "accepted" else update_beliefs_rejected
    return fn(npc, trade)

def update_beliefs_accepted(npc, trade_history, trade):
    mean = avg_price(trade.resource, trade_history)
    interval = getattr(npc.belief_intervals, trade.resource)
    if not (.66 < (trade.price/mean) < 1.33):
        interval = translate_interval(interval, mean)

    interval = shrink_interval(interval)

    npc = npc._replace(belief_intervals=npc.belief_intervals._replace(**{trade.resource: interval}))
    return npc

def update_beliefs_rejected(npc, trade_history, trade):
    mean = avg_price(trade.resource, trade_history)
    interval = getattr(npc.belief_intervals, trade.resource)
    interval = translate_interval(interval, mean)
    interval = expand_interval(interval)

    npc = npc._replace(belief_intervals=npc.belief_intervals._replace(**{trade.resource: interval}))
    return npc


def get_sell_resource(occupation):
    return dict(
        farmer="food",
        lumberjack="wood",
        miner="ore",
        refiner="metal",
    )[occupation]


def get_buy_resources(occupation):
    return dict(
        farmer = ["wood", "tools"],
        lumberjack = ["food", "tools"],
        miner = ["food", "tools"],
        refiner = ["food", "ore", "tools"],
        blacksmith = ["metal"],
    )[occupation]


def create_ask(npc, resource):
    price = estimate_npc_price(resource, npc.belief_intervals)
    num_to_sell = max(limit, ideal)


def determine_sale_quantity(npc, price):
    resource = get_sell_resource(occupation)
    mean = avg_price()

def determine_purchase_quantity(npc):
    resources = get_purchaser_resources(occupation)
    mean = avg_price()
