import sys
import os
import ctypes
import winreg

"""Class to extract system information from a MS-Windows Box:

Instructions for Using:

Instance the class WindowsSystemInformation
Then in the instance, access the following variables:

os
cpu
totalRAM
totalVM
availableVM
availableRAM
extendedVM

Example:

s = SystemInformation()
print(s.os)

s.refresh() # if you need to refresh the dynamic data (i.e. Memory stats, etc)
"""

def get_registry_value(key, subkey, value):
    if sys.platform != 'win32':
        raise OSError("get_registry_value is only supported on Windows")
        
    key = getattr(winreg, key)
    handle = winreg.OpenKey(key, subkey)
    (value, type) = winreg.QueryValueEx(handle, value)
    return value

c_ulong = ctypes.c_ulong

class MEMORYSTATUS(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_long),
        ('dwMemoryLoad', ctypes.c_long),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
    ]

class SystemInformation:
    def __init__(self):

        # Just in in case somebody called this class by accident, we should
        # check to make sure the OS is MS-Windows before continuing.

        assert sys.platform == 'win32', "Not an MS-Windows Computer. This class should not be called"
        
        # os contains the Operating System Name with Service Pack and Build
        # Example: Microsoft Windows XP Service Pack 2 (build 2600)
        
        self.os = self._os_version().strip()
        
        # cpu contains the CPU model and speed
        # Example: Intel Core(TM)2 CPU 6700 @ 2.66GHz

        self.cpu = self._cpu().strip()

        self.totalRAM, self.availableRAM, self.totalPF, self.availablePF, self.memoryLoad, self.totalVM, self.availableVM, self.extendedVM = self._ram()

        # totalRam contains the total amount of RAM in the system

        self.totalRAM = self.totalRAM / 1024

        # totalVM contains the total amount of VM available to the system
        
        self.totalVM = self.totalVM / 1024

        # availableVM contains the amount of VM that is free
        
        self.availableVM = self.availableVM / 1024

        # availableRam: Amount of available RAM in the system
        
        self.availableRAM = self.availableRAM / 1024

        # extendedVM: Amount of available extended VM in the system

        self.extendedVM = self.extendedVM / 1024

    def refresh(self):
         self.totalRAM, self.availableRAM, self.totalPF, self.availablePF, self.memoryLoad, self.totalVM, self.availableVM, self.extendedVM = self._ram()
         self.totalRAM = self.totalRAM / 1024
         self.totalVM = self.totalVM / 1024
         self.availableVM = self.availableVM / 1024
         self.availableRAM = self.availableRAM / 1024
         self.extendedVM = self.extendedVM / 1024

    def _os_version(self):
        def get(key):
            return get_registry_value(
                "HKEY_LOCAL_MACHINE", 
                "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                key)
        os = get("ProductName")
        # Used to be CSDVersion, doesn't work on modern OS
        sp = get("DisplayVersion")
        build = get("CurrentBuildNumber")
        return "%s %s (build %s)" % (os, sp, build)
            
    def _cpu(self):
        return get_registry_value(
            "HKEY_LOCAL_MACHINE", 
            "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0",
            "ProcessorNameString")
            
    def _ram(self):
        kernel32 = ctypes.windll.kernel32
        

        memoryStatus = MEMORYSTATUS()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
        return (memoryStatus.ullTotalPhys, memoryStatus.ullAvailPhys, memoryStatus.ullTotalPageFile, memoryStatus.ullAvailPageFile, memoryStatus.dwMemoryLoad, memoryStatus.ullTotalVirtual, memoryStatus.ullAvailVirtual, memoryStatus.ullAvailExtendedVirtual)

# To test, execute the script standalone.

if __name__ == "__main__":
    s = SystemInformation()
    print(s.os)
    print(s.cpu)
    print("RAM : %dKb total" % s.totalRAM)
    print("RAM : %dKb free" % s.availableRAM)
    print("Total VM: %dKb" % s.totalVM)
    print("Available VM: %dKb" % s.availableVM)
    print("Extended VM: %dKb (Always returns 0))" % s.extendedVM)
