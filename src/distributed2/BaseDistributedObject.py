
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify

from .DOState import DOState

# Base network object class
class BaseDistributedObject(DirectObject):
    notify = directNotify.newCategory("BaseDistributedObject")

    """
    DO lifetime

    In order to implement distributed objects, we need to have:
    A generate message - gets sent to all clients in the world when an object
                         comes into existance
    Event messages - when something interesting happens to the object
    Update messages - when something intersting changes on the object
    A delete message - when the object goes away

    __init__():
    Brand new object is being constructed but isn't "alive" yet

    generate():
    Brand new object is now alive but does not have a known initial state

    announceGenerate(): client only
    Object has a known initial state and is now fully alive... OR the object
    was temporarily disabled/cached away and is coming back. Start things like
    tasks, event listeners, and add the object into the scene graph.

    disable(): client only
    Object is being temporarily removed/cached away to quickly bring it back
    when requested. Clean up all logical things like tasks, event listeners,
    and remove it from the scene graph.. but don't delete nodes/data from memory.

    delete():
    Object is going away completely, should tear down everything created in
    generate() and __init__() expecting the object to never come back.

    """

    def __init__(self):
        self.doId = None
        self.zoneId = None
        self.dclass = None
        self.doState = DOState.Fresh
        # Set of tasks that have been created on this object.
        self._tasks = {}

    def isGenerated(self):
        return self.doState >= DOState.Generated

    def isAlive(self):
        return self.doState >= DOState.Alive

    def isDisabled(self):
        return self.doState <= DOState.Disabled

    def isFresh(self):
        return self.doState == DOState.Fresh

    def isDeleted(self):
        return self.doState == DOState.Deleted

    def addTask(self, method, name, extraArgs = [], appendTask = False, sim = True):
        """
        Convenience method to create a task for this distributed object.

        If sim is True (the default), the task will be added onto the
        simulation task manager, which runs once per simulation tick.

        If sim is False, the task will be added onto the regular task manager,
        which runs once per frame.
        """

        mgr = base.simTaskMgr if sim else base.taskMgr

        task = mgr.add(method, self.taskName(name), extraArgs = extraArgs, appendTask = appendTask)
        self._tasks[name] = (task, mgr)
        return task

    def removeTask(self, name, removeFromTable = True):
        """
        Removes the task from the object by name.
        """

        taskInfo = self._tasks.get(name, None)
        if taskInfo:
            task = taskInfo[0]
            task.remove()
            if removeFromTable:
                del self._tasks[name]

    def removeAllTasks(self):
        """
        Removes all tasks that have been created for this object.
        """
        for taskInfo in self._tasks.values():
            task = taskInfo[0]
            task.remove()
        self._tasks = {}

    def uniqueName(self, name):
        """
        Returns a unique identifier for the given name.
        """

        return "%s-%i" % (name, self.doId)

    def taskName(self, name):
        """
        Returns a unique task identifier for the given name.
        """

        return self.uniqueName(name)

    def sendUpdate(self, name, args = []):
        """
        Sends a non-stateful event message from one object view to another.
        """
        pass

    def update(self):
        """ Called once per tick to simulate object. """
        pass

    def generate(self):
        """ Called when the object has first come into existence. At the time
        of this call on the client, the baseline state of the object has not
        yet been applied. """

        self.doState = DOState.Generated

    def announceGenerate(self):
        """ See DistributedObject.py for the reason of this method. It only
        exists here to set the state to alive. """
        self.doState = DOState.Alive

    def delete(self):
        """ Object is going away for good. Clean up everything completely
        here. Clean up stuff that was created in __init__ or generate """

        self.ignoreAll()
        self.removeAllTasks()
        self._tasks = None
        self.doId = None
        self.zoneId = None
        self.dclass = None
        self.doState = DOState.Deleted
