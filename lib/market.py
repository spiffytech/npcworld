from collections import namedtuple
from functools import partial

# Look at ways to set default values on namedtuples from http://stackoverflow.com/questions/11351032/named-tuple-and-optional-keyword-arguments

Market = namedtuple("Market", ["bid", "ask"])
Inventory = namedtuple("Inventory", ["wood", "food", "ore", "metal", "tools"])
Inventory.__new__ = partial(Inventory.__new__, wood=10, food=10, ore=10, metal=10, tools=10)

ResourceDelta = namedtuple("ResourceDelta", ["wood", "food", "ore", "metal", "tools"])
ResourceDelta.__new__ = partial(ResourceDelta.__new__, wood=0, food=0, ore=0, metal=0, tools=0)

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

NPC = namedtuple("NPC", ["occupation", "inventory"], True)
NPC.__new__ = partial(
    NPC.__new__,
    occupation=None,
    inventory=Inventory(),
)

def miner_produce(npc):
    inventory = npc.inventory
    print inventory
    if has_food(inventory) and has_tools(inventory):
        delta = dict(food=inventory.food-1, ore=inventory.ore+4)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)
        
def farmer_produce(npc):
    inventory = npc.inventory
    if has_wood(inventory) and has_tools(inventory):
        delta = dict(wood=inventory.wood-1, food=inventory.food+4)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)

def lumberjack_produce(npc):
    inventory = npc.inventory
    if has_food(inventory) and has_tools(inventory):
        delta = dict(food=inventory.food-1, wood=inventory.wood+4)
        inventory = inventory._replace(**delta)
    return npc._replace(inventory=inventory)
