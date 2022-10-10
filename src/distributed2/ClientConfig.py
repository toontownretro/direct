from panda3d.core import ConfigVariableInt, ConfigVariableDouble, ConfigVariableBool

cl_cmdrate = ConfigVariableInt("cl_cmdrate", 100)
cl_updaterate = ConfigVariableInt("cl_updaterate", 20)
cl_interp = ConfigVariableDouble("cl_interp", 0.1)
cl_interp_ratio = ConfigVariableDouble("cl_interp_ratio", 2)
# Should we ping the server every so often to measure latency?
cl_ping = ConfigVariableBool("cl_ping", True)
# How often we ping the server to measure latency.
cl_ping_interval = ConfigVariableDouble("cl_ping_interval", 10.0)
# Should we print the latest ping measurement to console?
cl_report_ping = ConfigVariableBool("cl_report_ping", True)

def getClientInterpAmount():
    return max(cl_interp.getValue(), cl_interp_ratio.getValue() / float(cl_updaterate.getValue()))
