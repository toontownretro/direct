from panda3d.core import ConfigVariableBool, ConfigVariableString, ConfigVariableInt

# Server related config variables
sv_max_clients = ConfigVariableInt("sv_max_clients", 24)
sv_password = ConfigVariableString("sv_password", "")
sv_minupdaterate = ConfigVariableInt("sv_minupdaterate", 1)
sv_maxupdaterate = ConfigVariableInt("sv_maxupdaterate", 255)
sv_tickrate = ConfigVariableInt("sv_tickrate", 66)
# How many past snapshots do we save?
sv_snapshot_history = ConfigVariableInt("sv_snapshot_history", 50)
sv_port = ConfigVariableInt("sv_port", 27015)
sv_alternateticks = ConfigVariableBool("sv_alternateticks", False)
