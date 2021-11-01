from panda3d.core import ConfigVariableInt, ConfigVariableDouble

cl_cmdrate = ConfigVariableInt("cl_cmdrate", 100)
cl_updaterate = ConfigVariableInt("cl_updaterate", 20)
cl_interp = ConfigVariableDouble("cl_interp", 0.1)
cl_interp_ratio = ConfigVariableDouble("cl_interp_ratio", 2)

def getClientInterpAmount():
    return max(cl_interp.getValue(), cl_interp_ratio.getValue() / cl_updaterate.getValue())
