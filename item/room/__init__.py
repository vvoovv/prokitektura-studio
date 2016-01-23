from base import pContext
from item.area import Area


class Room(Area):
    type = "room"
    name = "Room"


pContext.register(Room, None)