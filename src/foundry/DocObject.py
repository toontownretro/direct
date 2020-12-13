class DocObject:
    """
    This is the class that all document classes should inherit from
    """

    def __init__(self, doc = None):
        self.doc = doc

    def setDoc(self, doc):
        self.doc = doc

    def cleanup(self):
        self.ignoreAll()
        self.ignoreAllGlobal()
        self.doc = None
        self.removeAllTasks()
        self._taskList = None

    #def __del__(self):
        # This next line is useful for debugging leaks
        #print "Destructing: ", self.__class__.__name__

    # Wrapper functions to have a cleaner, more object oriented approach to
    # the messenger functionality.

    def send(self, event, extraArgs=[]):
        if not self.doc:
            return
        self.doc.messenger.send(event, extraArgs)

    def sendGlobal(self, event, extraArgs=[]):
        messenger.send(event, extraArgs)

    def accept(self, event, method, extraArgs=[]):
        if not self.doc:
            return None
        return self.doc.messenger.accept(event, self, method, extraArgs, 1)

    def acceptGlobal(self, event, method, extraArgs=[]):
        return messenger.accept(event, self, method, extraArgs, 1)

    def acceptOnce(self, event, method, extraArgs=[]):
        if not self.doc:
            return None
        return self.doc.messenger.accept(event, self, method, extraArgs, 0)

    def acceptOnceGlobal(self, event, method, extraArgs=[]):
        return messenger.accept(event, self, method, extraArgs, 0)

    def ignore(self, event):
        if not self.doc:
            return None
        return self.doc.messenger.ignore(event, self)

    def ignoreGlobal(self, event):
        return messenger.ignore(event, self)

    def ignoreAll(self):
        if not self.doc:
            return None
        return self.doc.messenger.ignoreAll(self)

    def ignoreAllGlobal(self):
        return messenger.ignoreAll(self)

    def isAccepting(self, event):
        if not self.doc:
            return None
        return self.doc.messenger.isAccepting(event, self)

    def getAllAccepting(self):
        if not self.doc:
            return None
        return self.doc.messenger.getAllAccepting(self)

    def isIgnoring(self, event):
        if not self.doc:
            return None
        return self.doc.messenger.isIgnoring(event, self)

    #This function must be used if you want a managed task
    def addTask(self, *args, **kwargs):
        if not self.doc:
            return None
        if(not hasattr(self,"_taskList")):
            self._taskList = {}
        kwargs['owner']=self
        task = self.doc.taskMgr.add(*args, **kwargs)
        return task

    def doMethodLater(self, *args, **kwargs):
        if not self.doc:
            return None
        if(not hasattr(self,"_taskList")):
            self._taskList ={}
        kwargs['owner']=self
        task = self.doc.taskMgr.doMethodLater(*args, **kwargs)
        return task

    def removeTask(self, taskOrName):
        if type(taskOrName) == type(''):
            # we must use a copy, since task.remove will modify self._taskList
            if hasattr(self, '_taskList'):
                taskListValues = list(self._taskList.values())
                for task in taskListValues:
                    if task.name == taskOrName:
                        task.remove()
        else:
            taskOrName.remove()

    def removeAllTasks(self):
        if hasattr(self,'_taskList'):
            for task in list(self._taskList.values()):
                task.remove()

    def _addTask(self, task):
        self._taskList[task.id] = task

    def _clearTask(self, task):
        del self._taskList[task.id]
