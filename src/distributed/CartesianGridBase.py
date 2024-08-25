from panda3d.core import Vec3, NodePath
from .GridChild import GridChild

class CartesianGridBase:
    # Utility functions that are useful to both AI and client CartesianGrid code

    def __init__(self, startingZone = 500, gridSize = 100, gridRadius = 3, cellWidth = 50, style="Cartesian", period = 0):
        self.startingZone = startingZone
        self.gridSize = gridSize
        self.gridRadius = gridRadius
        self.cellWidth = cellWidth
        self.style = style
        self.center = gridSize * cellWidth / 2.0
        
        self.__managedChildren = set()
        self.__managementTask = None
        self.__period = period
        pass

    def disable(self):
        self.stopManagementTask()
        self.__managedChildren.clear()
        pass

    def isGrid(self):
        return True

    def setParentingRules(self, style, rule):
        rules = rule.split(':')
        assert len(rules) == 3
        self.style = style
        self.startingZone = int(rules[0])
        self.gridSize = int(rules[1])
        self.viewingRadius = int(rules[2])
        self.center = self.gridSize * self.cellWidth / 2.0
        pass

    def getParentingRules(self):
        rule = ("%i:%i:%i" % (self.startingZone, self.gridSize, self.gridRadius))
        return [self.style, rule]

    def getCellWidth(self):
        return self.cellWidth
    
    def setCellWidth(self, width):
        self.cellWidth = width

    def isValidZone(self, zoneId):
        
        if self.style == "Cartesian":
            return self.isGridZone(zoneId)
        elif self.style == "CartesianStated":
            return (0 <= zoneId < self.startingZone) or \
                   self.isGridZone(zoneId)
        else:
            assert False, "Unrecognized 'style'"
            return False

    def isGridZone(self, zoneId):
        return self.startingZone <= zoneId < (self.startingZone + self.gridSize * self.gridSize)
        
    def getZoneFromXYZ(self, pos, wantRowAndCol=False):
        # NOTE: pos should be relative to our own grid origin
        # Convert a 3d position to a zone
        x = pos[0] + self.center
        y = pos[1] + self.center
        col = x // self.cellWidth
        row = y // self.cellWidth
        # Compute which zone we are in
        zoneId = int(self.startingZone + ((row * self.gridSize) + col))

        if wantRowAndCol:
            return (zoneId, col, row)
        else:
            return zoneId

    def getZoneAndCellPosFromXYZ(self, pos):
        zone = self.getZoneFromXYZ(pos)
        x = pos[0] % self.cellWidth
        y = pos[1] % self.cellWidth
        return zone, Vec3(x, y, pos[2])

    def getGridSizeFromSphereRadius(self, sphereRadius, cellWidth, gridRadius):
        # NOTE: This ensures that the grid is at least a "gridRadius" number
        # of cells larger than the trigger sphere that loads the grid.  This
        # gives us some room to start setting interest to the grid before we
        # expect to see any objects on it.
        sphereRadius = max(sphereRadius, gridRadius*cellWidth)
        return 2 * (sphereRadius // cellWidth)

    def getGridSizeFromSphere(self, sphereRadius, spherePos, cellWidth, gridRadius):
        # NOTE: This ensures that the grid is at least a "gridRadius" number
        # of cells larger than the trigger sphere that loads the grid.  This
        # gives us some room to start setting interest to the grid before we
        # expect to see any objects on it.
        xMax = abs(spherePos[0])+sphereRadius
        yMax = abs(spherePos[1])+sphereRadius
        sphereRadius = Vec3(xMax,yMax,0).length()
        
        # sphereRadius = max(sphereRadius, gridRadius*cellWidth)
        return max(2 * (sphereRadius // cellWidth), 1)

    def getZoneCellOrigin(self, zoneId):
        # It returns the origin(bottom-left) of the zoneCell
        zone = zoneId - self.startingZone
        row = zone // self.gridSize
        col = zone % self.gridSize
        x = col * self.cellWidth - self.center
        y = row * self.cellWidth - self.center

        return (x, y, 0)

    def getZoneCellOriginCenter(self, zoneId):
        # Variant of the getZoneCellOrigin. It
        # returns the center of the zoneCell
        x,y,z = self.getZoneCellOrigin(zoneId)
        center = self.cellWidth * 0.5
        return (x+center, y+center, z)

    #--------------------------------------------------------------------------
    # Function:   utility function to get all zones in a ring of given radius
    #               around the given zoneId (so if given a zoneId 34342 and a
    #               radius of 3, a list of all zones exactly 3 grids away from
    #               zone 34342 will be returned)
    # Parameters: zoneId, center zone to find surrounding zones of
    #             radius, how far from zoneId to find zones of for it them
    # Changes:
    # Returns:
    #--------------------------------------------------------------------------
    def getConcentricZones(self, zoneId, radius):
        zones = []
        #currZone = zoneId + radius
        #numZones = (2 * radius * 8) + 2
        # start at upper left
        zone = zoneId - self.startingZone
        row = zone // self.gridSize
        col = zone % self.gridSize

        leftOffset = min(col, radius)
        rightOffset = min(self.gridSize - (col + 1), radius)
        topOffset = min(row, radius)
        bottomOffset = min(self.gridSize - (row + 1), radius)

        #print "starting examination of grid circle of radius %s"%radius
        ulZone = zoneId - leftOffset - topOffset * self.gridSize
        #print "left offset is %s and radius is %s"%(leftOffset,radius)
        for currCol in range(int(rightOffset + leftOffset + 1)):
            if ((currCol == 0 and leftOffset == radius) or (currCol == rightOffset + leftOffset and rightOffset == radius)):
                # at either left or right edge of area, look at all rows
                possibleRows = range(int(bottomOffset + topOffset + 1))
            else:
                # in a middle column, only look at top and bottom rows
                possibleRows = []
                if topOffset == radius:
                    possibleRows.append(0)
                if bottomOffset == radius:
                    possibleRows.append(bottomOffset + topOffset)
            #print "on column %s and looking at rows %s"%(currCol,possibleRows)
            for currRow in possibleRows:
                newZone = ulZone + (currRow * self.gridSize) + currCol
                zones.append(int(newZone))
                #print "   examining zone %s"%newZone
        return zones

    #--------------------------------------------------------------------------
    # Function:   child has been parented to this grid, set zone interest
    #               for this area, and can be overridden to add additional
    #               interest (such as interest on the parent grid of this
    #               area)
    # Parameters:
    # Changes:
    # Returns:
    #--------------------------------------------------------------------------
    def setChildGridCells(self, child, zoneId):
        child.setGridCell(self, zoneId)

    def parentObjectToArea(self, child):
        """
        Assumes the child is either parented directly to the grid or detached
        and has the desired absolute position wrt the grid.
        This attaches the child to the grid with a grid cell node in-between.
        The relative transform between the child and grid is maintained.
        """
        assert isinstance(child, GridChild), "Must be a GridChild to do this"
        assert not child.getParent() or child.getParent() == NodePath(self), "Parent must be grid or None"
        child.reparentTo(self) # go ahead and put us here
        zoneId = self.getZoneFromXYZ(child.getPos())
        if self.isGridZone(zoneId):
            self.setChildGridCells(child, zoneId)
            return zoneId
        else:
            assert self.notify.warning("Placing object on grid in non-grid zone(%s): %s" % (zoneId, child))
        return 0            

    def handleChildArrive(self, child, zoneId):
        assert isinstance(child, GridChild), "Must be a GridChild to be setLocation()ed here"
        if self.isGridZone(zoneId):
            child.setGridCell(self, zoneId)
        else:
            child.setGridCell(None, 0)

    def handleChildLeave(self, child, zoneId):
        self.ignoreChild(child)
        child.setGridCell(None, 0)

    def manageChild(self, child):
        """
        This will cause the grid to track this child object as it moves across
        the cells.  When a boundary is crossed, it will call child.setGridCell() and
        child.b_setLocation() with the new grid cell info.
        """
        assert child, "Must have a non-empty nodepath"
        assert child.getGrid() is self, "Must have already been setGridCell()'ed to me"
        self.__managedChildren.add(child)
        self.__manageChild(child, setup = True)
        if not self.__managementTask:
            self.startManagementTask()

    def isManagedChild(self, child):
        """
        Ask if given child is currently managed by this grid
        """
        return child in self.__managedChildren

    def ignoreChild(self, child):
        """
        Stops managing this child.
        """
        self.__managedChildren.discard(child)
        if not self.__managedChildren:
            self.stopManagementTask()
    
    def startManagementTask(self):
        self.stopManagementTask()
        if self.__period:
            self.__managementTask = taskMgr.doMethodLater(self.__period, self.__manage,
                                                          self.taskName('ManageGrid'))
            self.__managementTask._return = self.__managementTask.again
        else:
            self.__managementTask = taskMgr.add(self.__manage,
                                                self.taskName('ManageGrid'))
            self.__managementTask._return = self.__managementTask.cont

    def __manage(self, task):

        # Want to be clever?
        # map(__manageChild, self.__managedChildren)
        #  or 
        # [self.__manageChild(child) for child in self.__managedChildren]
        
        for child in self.__managedChildren:
            self.__manageChild(child)
        return task._return

    #--------------------------------------------------------------------------
    # Function:   determine if given child has a valid interest on the given
    #               grid
    # Parameters:
    # Changes:
    # Returns:
    #--------------------------------------------------------------------------
    def validGridInterest(self, child, gridId):
        return True

    def __manageChild(self, child, setup = False):
        assert child, "Must have a non-empty nodepath"
        assert child.getGrid() is self

        # manage all grid interests this child has
        gridIds = child.getGridInterestIds()
        for currGridId in gridIds:
            currGrid = getBase().getRepository().doId2do.get(currGridId)
            if not currGrid:
                # grid is gone or this client is cleaned up, ignore
                continue
            adjustGrid = False
            newZoneId = None
            if currGrid is self:
                # this grid is me, the one the child is parented to, so
                # just check if child is out of bounds of its current zone
                x,y,z = child.getPos()
                if x < 0 or y < 0 or \
                   x > currGrid.cellWidth or y > currGrid.cellWidth or \
                   setup:
                    adjustGrid = True
            else:
                # this grid is not me, need to determine if relative position
                # would put it in a different zone than it previously
                # registered interest in
                newZoneId = currGrid.getZoneFromXYZ(child.getPos(currGrid))
                if newZoneId != child.getGridInterestZoneId(currGridId):
                    adjustGrid = True

            if adjustGrid:
                # need to update zone child is in (or at least interested in)
                if not newZoneId:
                    newZoneId = currGrid.getZoneFromXYZ(child.getPos(currGrid))

                if currGrid.isGridZone(newZoneId):
                    if currGrid is self:
                        child.setGridCell(self, newZoneId, updateInterest=True)
                        # have to verify new position? were getting some crashes
                        # where ncps would be out of range
                        # TODO: add logging info to determine where object is and
                        # what state they are in
                        child.checkPosition()
                        child.sendCurrentPosition()
                        if not self.validGridInterest(child, currGridId):
                            # i am on a client and this grid interest is not registered
                            # with the server so we cannot perform any actual set location
                            self.notify.warning("skipping setLocation with child %s and grid %s"%(
                                child,currGridId))
                            continue
                        # for debugging...only in QA so we can test disconnect bug,
                        # can remove if solved
                        if (config.GetBool('print-interest-debug', 1) and
                            game.process == 'client' and
                            launcher.getValue("GAME_ENVIRONMENT", "DEV") in ["QA","DEV"]):
                            base.cr.printInterestSets()
                            self.notify.warning("pre-setLocation: interests from child %s are %s"%(
                                child.doId,child._gridInterests))
                        child.b_setLocation(self.getDoId(), newZoneId)
                    else:
                        # not my parent grid, just update interest
                        child.updateGridInterest(currGrid, newZoneId)
                else:
                    self.notify.warning(
                        "%s handleChildCellChange %s: not a valid zone (%s) for pos %s" %(
                        self.doId, child.doId, newZoneId, child.getPos(currGrid)))                     

    def stopManagementTask(self):
        if self.__managementTask:
            taskMgr.remove(self.__managementTask)
        self.__managementTask = None

    def taskName(self, taskString):
        assert False, "Subclasses must define this"

    def forceManagePass(self,child,setup=False):
        if child in self.__managedChildren:
            self.__manageChild(child, setup = setup)
