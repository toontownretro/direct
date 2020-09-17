from enum import IntEnum

class DOState:

    Deleted   = 0 # completely gone
    Disabled  = 1 # cached away
    Fresh     = 2 # before generate
    Generated = 3 # before announceGenerate
    Alive     = 4 # announceGenerate and alive
