"""Contains the global :class:`~.Task.TaskManager` object."""

__all__ = ['taskMgr']

from . import Task

#: The global task manager.
taskMgr = Task.TaskManager()
#: The global task manager that runs fixed-step simulations.
from panda3d.core import AsyncTaskManager
simTaskMgr = Task.TaskManager()
simTaskMgr.mgr = AsyncTaskManager("simulation")
