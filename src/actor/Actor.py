"""Actor module: contains the Actor class.

See the :ref:`loading-actors-and-animations` page in the Programming Guide
to learn more about loading animated models.
"""

__all__ = ['Actor']

from panda3d.core import *
from panda3d.core import Loader as PandaLoader

from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader

class Actor(DirectObject, NodePath):
    """Actor re-implementation using the new animation system."""

    notify = DirectNotifyGlobal.directNotify.newCategory("Actor")
    partPrefix = "__Actor_"

    modelLoaderOptions = LoaderOptions(LoaderOptions.LFSearch |
                                       LoaderOptions.LFReportErrors |
                                       LoaderOptions.LFConvertSkeleton)
    animLoaderOptions =  LoaderOptions(LoaderOptions.LFSearch |
                                       LoaderOptions.LFReportErrors |
                                       LoaderOptions.LFConvertAnim)

    class AnimDef:
        """Information about a single animation of a part."""

        def __init__(self, filename = None, channel = None, char = None):
            self.filename = filename
            self.name = ""
            self.channel = channel
            # Associated character.
            self.char = char
            # Index of the channel on the associated part character.
            self.index = -1
            # Have to store play rate here because the character does not
            # remember play rates of channels as they are set on layers.
            self.playRate = 1.0

        def isBound(self):
            return self.index >= 0

        def makeCopy(self, partDef):
            """
            Returns a copy of the AnimDef for use with the indicated PartDef.
            """
            animDef = Actor.AnimDef()
            if self.filename is not None:
                animDef.filename = Filename(self.filename)
            animDef.name = str(self.name)
            animDef.channel = self.channel
            animDef.char = partDef.char
            animDef.index = self.index
            animDef.playRate = self.playRate
            partDef.animsByName[animDef.name] = animDef
            if animDef.isBound():
                partDef.animsByIndex[animDef.index] = animDef

    class PartDef:
        """Maintains the objects for a particular "part" of the actor."""

        def __init__(self, charNP, char, partModel):
            self.charNP = charNP
            self.char = char
            self.partModel = partModel
            # Mapping of anim name to AnimDef
            self.animsByName = {}
            # Mapping of channel index to AnimDef
            self.animsByIndex = {}
            self.weightLists = {}

        def getChannelIndex(self, animName):
            animDef = self.animsByName.get(animName)
            if not animDef:
                return -1
            return animDef.index

        def getAnimDef(self, animName):
            if isinstance(animName, str):
                return self.animsByName.get(animName)
            return self.animsByIndex.get(animName)

    def __init__(self, models=None, anims=None, other=None, copy=True,
                 lodNode=None, flattenable=True, setFinal=False,
                 okMissing=None):
        try:
            self.Actor_initialized
            return
        except:
            self.Actor_initialized = 1

        NodePath.__init__(self)

        self.loader = PandaLoader.getGlobalPtr()

        self.__partBundleDict = {}
        self.__sortedLODNames = []

        self.__LODNode = None
        self.__LODAnimation = None
        self.__LODCenter = Point3(0, 0, 0)
        self.switches = None

        if other is None:
            # act like a normal constructor

            # create base hierarchy
            self.gotName = 0

            if flattenable:
                # If we want a flattenable Actor, don't create all
                # those ModelNodes, and the GeomNode is the same as
                # the root.
                root = PandaNode('actor')
                self.assign(NodePath(root))
                self.setGeomNode(NodePath(self))

            else:
                # A standard Actor has a ModelNode at the root, and
                # another ModelNode to protect the GeomNode.
                root = ModelRoot('actor')
                root.setPreserveTransform(1)
                self.assign(NodePath(root))
                self.setGeomNode(self.attachNewNode(ModelNode('actorGeom')))

            self.__hasLOD = 0

            # load models
            #
            # four cases:
            #
            #   models, anims{} = single part actor
            #   models{}, anims{} =  single part actor w/ LOD
            #   models{}, anims{}{} = multi-part actor
            #   models{}{}, anims{}{} = multi-part actor w/ LOD
            #
            # make sure we have models
            if models:
                # do we have a dictionary of models?
                if type(models) == dict:
                    # if this is a dictionary of dictionaries
                    if type(models[next(iter(models))]) == dict:
                        # then it must be a multipart actor w/LOD
                        self.setLODNode(node = lodNode)
                        # preserve numerical order for lod's
                        # this will make it easier to set ranges
                        sortedKeys = list(models.keys())
                        sortedKeys.sort()
                        for lodName in sortedKeys:
                            # make a node under the LOD switch
                            # for each lod (just because!)
                            self.addLOD(str(lodName))
                            # iterate over both dicts
                            for modelName in models[lodName]:
                                self.loadModel(models[lodName][modelName],
                                               modelName, lodName, copy = copy,
                                               okMissing = okMissing)
                    # then if there is a dictionary of dictionaries of anims
                    elif type(anims[next(iter(anims))]) == dict:
                        # then this is a multipart actor w/o LOD
                        for partName in models:
                            # pass in each part
                            self.loadModel(models[partName], partName,
                                           copy = copy, okMissing = okMissing)
                    else:
                        # it is a single part actor w/LOD
                        self.setLODNode(node = lodNode)
                        # preserve order of LOD's
                        sortedKeys = list(models.keys())
                        sortedKeys.sort()
                        for lodName in sortedKeys:
                            self.addLOD(str(lodName))
                            # pass in dictionary of parts
                            self.loadModel(models[lodName], lodName=lodName,
                                           copy = copy, okMissing = okMissing)
                else:
                    # else it is a single part actor
                    self.loadModel(models, copy = copy, okMissing = okMissing)

            # load anims
            # make sure the actor has animations
            if anims:
                if len(anims) >= 1:
                    # if so, does it have a dictionary of dictionaries?
                    if type(anims[next(iter(anims))]) == dict:
                        # are the models a dict of dicts too?
                        if type(models) == dict:
                            if type(models[next(iter(models))]) == dict:
                                # then we have a multi-part w/ LOD
                                sortedKeys = list(models.keys())
                                sortedKeys.sort()
                                for lodName in sortedKeys:
                                    # iterate over both dicts
                                    for partName in anims:
                                        self.loadAnims(
                                            anims[partName], partName, lodName)
                            else:
                                # then it must be multi-part w/o LOD
                                for partName in anims:
                                    self.loadAnims(anims[partName], partName)
                    elif type(models) == dict:
                        # then we have single-part w/ LOD
                        sortedKeys = list(models.keys())
                        sortedKeys.sort()
                        for lodName in sortedKeys:
                            self.loadAnims(anims, lodName=lodName)
                    else:
                        # else it is single-part w/o LOD
                        self.loadAnims(anims)

        else:
            self.copyActor(other, True) # overwrite everything

        if setFinal:
            # If setFinal is true, the Actor will set its top bounding
            # volume to be the "final" bounding volume: the bounding
            # volumes below the top volume will not be tested.  If a
            # cull test passes the top bounding volume, the whole
            # Actor is rendered.

            # We do this partly because an Actor is likely to be a
            # fairly small object relative to the scene, and is pretty
            # much going to be all onscreen or all offscreen anyway;
            # and partly because of the Character bug that doesn't
            # update the bounding volume for pieces that animate away
            # from their original position.  It's disturbing to see
            # someone's hands disappear; better to cull the whole
            # object or none of it.
            self.__geomNode.node().setFinal(1)

    def makeWeightList(self, name, weights, partName='modelRoot', lodName=None):
        """
        Constructs a weight list that can be applied to channels to control
        which joints are influenced by a channel and how much.  This can be
        used to achieve partial-body animation.
        """
        desc = WeightListDesc(name)
        for jointName, weight in weights.items():
            desc.setWeight(jointName, weight)

        for partDef in self.getPartDefs(partName, lodName):
            partDef.weightLists[name] = WeightList(partDef.char, desc)

    def setAnimWeightList(self, animName, weightListName, partName='modelRoot', lodName=None):
        """
        Applies a previously created weight list to the animation channel with
        the indicated name.  The channel will use the indicated weight list to
        control the influence of the channel on a per-joint basis.
        """
        for partDef in self.getPartDefs(partName, lodName):
            weightList = partDef.weightLists.get(weightListName)
            if not weightList:
                continue
            animDef = partDef.getAnimDef(animName)
            if not animDef:
                continue
            if not animDef.isBound() and not self.loadAndBindAnim(partDef, animDef):
                continue
            animDef.channel.setWeightList(weightList)

    def loadAnims(self, anims, partName="modelRoot", lodName="lodRoot", loadNow = False):
        """loadAnims(self, string:string{}, string='modelRoot',
        string='lodRoot')
        Actor anim loader. Takes an optional partName (defaults to
        'modelRoot' for non-multipart actors) and lodName (defaults
        to 'lodRoot' for non-LOD actors) and dict of corresponding
        anims in the form animName:animPath{}

        If loadNow is True, the Actor will immediately load up all animations
        from disk into memory.  Otherwise, animations will only be loaded the
        first time they are accessed through the Actor.
        """
        reload = True
        if lodName == 'all':
            reload = False
            lodNames = list(self.switches.keys())
            lodNames.sort()
            for i in range(0, len(lodNames)):
                lodNames[i] = str(lodNames[i])
        else:
            lodNames = [lodName]

        assert Actor.notify.debug("in loadAnims: %s, part: %s, lod: %s" %
                                  (anims, partName, lodNames[0]))

        for animName, filename in anims.items():
            if not loadNow:
                # Just create an AnimDef that references no channel.
                # When we try to access the AnimDef it will load the channel
                # then and bind it.
                for lName in lodNames:
                    partDef = self.__partBundleDict[lName][partName]
                    char = partDef.char
                    animDef = Actor.AnimDef(filename, char=char)
                    animDef.name = animName
                    partDef.animsByName[animName] = animDef
            else:
                # Load the channel into memory immediately and bind it.
                channel = self.loadAnim(filename)
                if not channel:
                    continue
                for lName in lodNames:
                    partDef = self.__partBundleDict[lName][partName]
                    animDef = Actor.AnimDef(filename, channel, partDef.char)
                    animDef.name = animName
                    partDef.animsByName[animName] = animDef
                    if not self.bindAnim(partDef, animDef, channel):
                        Actor.notify.warning("Failed to bind anim (" + animName + ", " + filename + ") to part " + partName + ", lod " + lName)

    def loadAnim(self, filename):
        """
        Loads a single animation from the indicated filename and returns the
        AnimChannel contained within it.  Returns None if an error occurred.
        If the file contains multiple channels, it only returns the first one.
        """

        animModel = self.loader.loadSync(filename, LoaderOptions())
        if not animModel:
            Actor.notify.warning("Failed to load animation file " + filename)
            return None

        animModelNP = NodePath(animModel)
        animBundleNP = animModelNP.find("**/+AnimChannelBundle")
        if animBundleNP.isEmpty():
            Actor.notify.warning("Model " + filename + " does not contain an animation!")
            return None
        animBundleNode = animBundleNP.node()
        # Add just the first channel within the bundle.
        # TODO: This will leave out other animations if there are multiple
        #       channels in the bundle.
        if animBundleNode.getNumChannels() > 1:
            Actor.notify.warning("Channel bundle " + filename + " contains multiple channels, using only the first one")
        elif animBundleNode.getNumChannels() == 0:
            Actor.notify.warning("Channel bundle " + filename + " contains no channels!")
            return None

        return animBundleNode.getChannel(0)

    def bindAnim(self, partDef, animDef, channel):
        """
        Given an already loaded channel, binds the channel to the character
        of the indicated part and stores the channel index on the indicated
        AnimDef.  Returns True if the channel was successfully bound and
        added to the part character, or False if there was an error.
        """

        if not partDef.char.bindAnim(channel):
            del partDef.animsByName[animDef.name]
            return False

        channelIndex = partDef.char.addChannel(channel)
        if channelIndex < 0:
            del partDef.animsByName[animDef.name]
            return False

        animDef.index = channelIndex
        animDef.channel = channel
        partDef.animsByIndex[channelIndex] = animDef

        return True

    def loadAndBindAnim(self, partDef, animDef):
        """
        Loads up the AnimChannel at the filename specified by the AnimDef and
        bind it to the Character of the PartDef.  Returns True on success, or
        False if the animation could not be loaded or bound.
        """

        channel = self.loadAnim(animDef.filename)
        if not channel:
            return False

        return self.bindAnim(partDef, animDef, channel)

    def loadModel(self, modelPath, partName="modelRoot", lodName="lodRoot",
                  copy = True, okMissing = None, autoBindAnims = True,
                  keepModel = False):
        """Actor model loader. Takes a model name (ie file path), a part
        name(defaults to "modelRoot") and an lod name(defaults to "lodRoot").
        """

        assert Actor.notify.debug("in loadModel: %s, part: %s, lod: %s, copy: %s" % \
                                  (modelPath, partName, lodName, copy))

        if isinstance(modelPath, NodePath):
            # If we got a NodePath instead of a string, use *that* as
            # the model directly.
            if copy:
                model = modelPath.copyTo(NodePath())
            else:
                model = modelPath
        else:
            # otherwise, we got the name of the model to load.
            loaderOptions = self.modelLoaderOptions
            if not copy:
                # If copy = 0, then we should always hit the disk.
                loaderOptions = LoaderOptions(loaderOptions)
                loaderOptions.setFlags(loaderOptions.getFlags() & ~LoaderOptions.LFNoRamCache)

            if okMissing is not None:
                if okMissing:
                    loaderOptions.setFlags(loaderOptions.getFlags() & ~LoaderOptions.LFReportErrors)
                else:
                    loaderOptions.setFlags(loaderOptions.getFlags() | LoaderOptions.LFReportErrors)

            # Ensure that custom Python loader hooks are initialized.
            Loader._loadPythonFileTypes()

            # Pass loaderOptions to specify that we want to
            # get the skeleton model.  This only matters to model
            # files (like .mb) for which we can choose to extract
            # either the skeleton or animation, or neither.
            model = self.loader.loadSync(Filename(modelPath), loaderOptions)
            if model is not None:
                model = NodePath(model)

        if model is None:
            raise IOError("Could not load Actor model %s" % (modelPath))

        if model.node().isOfType(CharacterNode.getClassType()):
            bundleNP = model
        else:
            bundleNP = model.find("**/+CharacterNode")

        if bundleNP.isEmpty():
            Actor.notify.warning("%s is not a character!" % (modelPath))
            model.reparentTo(self.__geomNode)
            return

        # Any animations and sequences that were bundled in with the model
        # should already exist on the Character at this point.

        # Now extract out the Character and integrate it with
        # the Actor.

        nodeToParent = model if keepModel else bundleNP

        if lodName != "lodRoot":
            # parent to appropriate node under LOD switch
            nodeToParent.reparentTo(self.__LODNode.find(str(lodName)))
        else:
            nodeToParent.reparentTo(self.__geomNode)
        self.__prepareBundle(bundleNP, model, partName, lodName)

        # we rename this node to make Actor copying easier
        bundleNP.node().setName("%s%s"%(Actor.partPrefix,partName))

        # Check for channels embedded in the model.  If there are any, add
        # them to the PartDefs dictionary of channels so they are visible
        # to the Actor.  Channels embedded in the Character are assumed to
        # be already bound.
        partDef = self.__partBundleDict[lodName][partName]
        for i in range(partDef.char.getNumChannels()):
            chan = partDef.char.getChannel(i)
            animDef = Actor.AnimDef(channel=chan, char=partDef.char)
            animDef.name = chan.getName()
            animDef.index = i
            partDef.animsByName[animDef.name] = animDef
            partDef.animsByIndex[i] = animDef

    def __prepareBundle(self, bundleNP, partModel,
                        partName="modelRoot", lodName="lodRoot"):
        # Rename the node at the top of the hierarchy, if we
        # haven't already, to make it easier to identify this
        # actor in the scene graph.
        if not self.gotName:
            self.node().setName(bundleNP.node().getName())
            self.gotName = 1

        bundleDict = self.__partBundleDict.get(lodName, None)
        if bundleDict is None:
            # make a dictionary to store these parts in
            bundleDict = {}
            self.__partBundleDict[lodName] = bundleDict
            self.__updateSortedLODNames()

        node = bundleNP.node()
        # A model loaded from disk will always have just one bundle.
        #assert(node.getNumBundles() == 1)
        bundleHandle = node.getCharacter()

        bundleDict[partName] = Actor.PartDef(bundleNP, bundleHandle, partModel)

    def setPlayRate(self, rate, anim=None, partName=None, layer=0):
        """setPlayRate(self, float, string, string=None)
        Set the play rate of given anim for a given part.
        If no part is given, set for all parts in dictionary.

        It used to be legal to let the animName default to the
        currently-playing anim, but this was confusing and could lead
        to the wrong anim's play rate getting set.  Better to insist
        on this parameter.
        NOTE: sets play rate on all LODs"""

        if anim is None:
            # Set play rate of layer for duration of currently playing channel.
            for partDef in self.getPartDefs(partName):
                animLayer = partDef.char.getAnimLayer(layer)
                if not animLayer:
                    continue
                animLayer._play_rate = rate

            return

        # Store permanent play rate on channel.
        for animDef in self.getAnimDefs(anim, partName):
            animDef.playRate = rate

            # If it's playing adjust the layer play rate.
            for i in range(animDef.char.getNumAnimLayers()):
                animLayer = animDef.char.getAnimLayer(i)
                if animLayer._sequence == animDef.index:
                    animLayer._play_rate = rate

    def getPlayRate(self, animName=None, partName=None, layer=0):
        """
        Return the play rate of given anim for a given part.
        If no part is given, assume first part in dictionary.
        If no anim is given, find the current anim for the part.
        NOTE: Returns info only for an arbitrary LOD
        """

        if animName is not None:
            # Return stored play rate of a channel.
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 1.0
            return animDefs[0].playRate

        if not self.__partBundleDict:
            return 1.0

        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        if partName:
            partDef = partBundleDict.get(partName)
            if not partDef:
                return 1.0
        else:
            partName, partDef = next(iter(partBundleDict.items()))

        # Return play rate of layer.
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return 1.0
        return animLayer._play_rate

    def getDuration(self, animName=None, partName=None,
                    fromFrame=None, toFrame=None, layer=0):
        """
        Return duration of given anim name and given part.
        If no anim specified, use the currently playing anim.
        If no part specified, return anim duration of first part.
        NOTE: returns info for arbitrary LOD
        """

        if animName is not None:
            # Return duration of a specific named channel.
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 0.1
            animDef = animDefs[0]
            chan = animDef.channel
            playRate = animDef.playRate
        else:
            # Return duration of current channel playing on a layer.
            if not self.__partBundleDict:
                return 0.1

            lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
            if partName:
                partDef = partBundleDict.get(partName)
                if not partDef:
                    return 0.1
            else:
                partName, partDef = next(iter(partBundleDict.items()))

            animLayer = partDef.char.getAnimLayer(layer)
            if not animLayer:
                return 0.1
            if animLayer._sequence == -1:
                return 0.1
            chan = partDef.char.getChannel(animLayer._sequence)
            playRate = animLayer._play_rate

        if fromFrame is None:
            fromFrame = 0
        if toFrame is None:
            toFrame = chan.getNumFrames() - 1

        return abs((((toFrame+1)-fromFrame) / chan.getFrameRate()) / playRate)

    def getNumFrames(self, animName=None, partName=None, layer=0):
        if animName is not None:
            # Return num frames of a specific channel.
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 1
            animDef = animDefs[0]
            return animDef.channel.getNumFrames()

        # Return num frames of a layer.
        for partDef in self.getPartDefs(partName):
            # Return num frames of a layer.
            animLayer = partDef.char.getAnimLayer(layer)
            if not animLayer:
                return 1
            if animLayer._sequence == -1:
                return 1
            return partDef.char.getChannel(animLayer._sequence).getNumFrames()

        return 1

    def getFrameRate(self, animName=None, partName=None, layer=0):
        """getFrameRate(self, string, string=None)
        Return actual frame rate of given anim name and given part.
        If no anim specified, use the currently playing anim.
        If no part specified, return anim durations of first part.
        NOTE: returns info only for an arbitrary LOD
        """
        if animName is not None:
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 1
            animDef = animDefs[0]
            return animDef.channel.getFrameRate() * animDef.playRate

        # Return frame rate of a layer.
        for partDef in self.getPartDefs(partName):
            animLayer = partDef.char.getAnimLayer(layer)
            if not animLayer or animLayer._sequence == -1:
                return 1
            return partDef.char.getChannel(animLayer._sequence).getFrameRate() * animLayer._play_rate

        return 1

    def getBaseFrameRate(self, animName=None, partName=None, layer=0):
        """getBaseFrameRate(self, string, string=None)
        Return frame rate of given anim name and given part, unmodified
        by any play rate in effect.
        """
        if animName is None:
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 1
            return animDefs[0].channel.getFrameRate()

        # Return frame rate of channel playing on a layer.
        for partDef in self.getPartDefs(partName):
            animLayer = partDef.char.getAnimLayer(layer)
            if not animLayer or animLayer._sequence == -1:
                return 1
            return partDef.char.getChannel(animLayer._sequence).getFrameRate()

        return 1

    def getFrameTime(self, anim, frame, partName=None):
        numFrames = self.getNumFrames(anim,partName)
        animTime = self.getDuration(anim,partName)
        frameTime = animTime * float(frame) / numFrames
        return frameTime

    def unloadAnims(self, anims=None, partName=None, lodName=None):
        """unloadAnims(self, string:string{}, string='modelRoot',
        string='lodRoot')
        Actor anim unloader. Takes an optional partName (defaults to
        'modelRoot' for non-multipart actors) and lodName (defaults to
        'lodRoot' for non-LOD actors) and list of animation
        names. Deletes the anim control for the given animation and
        parts/lods.

        If any parameter is None or omitted, it means all of them.
        """
        assert Actor.notify.debug("in unloadAnims: %s, part: %s, lod: %s" % (anims, partName, lodName))

    def getGeomNode(self):
        """
        Return the node that contains all actor geometry
        """
        return self.__geomNode

    def setGeomNode(self, node):
        """
        Set the node that contains all actor geometry
        """
        self.__geomNode = node

    def getLODNode(self):
        """
        Return the node that switches actor geometry in and out"""
        return self.__LODNode.node()

    def setLODNode(self, node=None):
        """
        Set the node that switches actor geometry in and out.
        If one is not supplied as an argument, make one
        """
        if node is None:
            node = LODNode.makeDefaultLod("lod")

        if self.__LODNode:
            self.__LODNode = node
        else:
            self.__LODNode = self.__geomNode.attachNewNode(node)
            self.__hasLOD = 1
            self.switches = {}

    def useLOD(self, lodName):
        """
        Make the Actor ONLY display the given LOD
        """
        # make sure we don't call this twice in a row
        # and pollute the the switches dictionary
        child = self.__LODNode.find(str(lodName))
        index = self.__LODNode.node().findChild(child.node())
        self.__LODNode.node().forceSwitch(index)

    def resetLOD(self):
        """
        Restore all switch distance info (usually after a useLOD call)"""
        self.__LODNode.node().clearForceSwitch()

    def hasLOD(self):
        """
        Return 1 if the actor has LODs, 0 otherwise
        """
        return self.__hasLOD

    def addLOD(self, lodName, inDist=0, outDist=0, center=None):
        """addLOD(self, string)
        Add a named node under the LODNode to parent all geometry
        of a specific LOD under.
        """
        self.__LODNode.attachNewNode(str(lodName))
        # save the switch distance info
        self.switches[lodName] = [inDist, outDist]
        # add the switch distance info
        self.__LODNode.node().addSwitch(inDist, outDist)
        if center is not None:
            self.setCenter(center)

    def setLOD(self, lodName, inDist=0, outDist=0):
        """setLOD(self, string)
        Set the switch distance for given LOD
        """
        # save the switch distance info
        self.switches[lodName] = [inDist, outDist]
        # add the switch distance info
        self.__LODNode.node().setSwitch(self.getLODIndex(lodName), inDist, outDist)

    def getLODIndex(self, lodName):
        """getLODIndex(self)
        safe method (but expensive) for retrieving the child index
        """
        return list(self.__LODNode.getChildren()).index(self.getLOD(lodName))

    def getLOD(self, lodName):
        """getLOD(self, string)
        Get the named node under the LOD to which we parent all LOD
        specific geometry to. Returns 'None' if not found
        """
        if not self.__LODNode:
            return None

        lod = self.__LODNode.find(str(lodName))
        if lod.isEmpty():
            return None

        return lod

    def update(self, lod=0, partName=None, lodName=None, force=False):
        """ Updates all of the Actor's joints in the indicated LOD.
        The LOD may be specified by name, or by number, where 0 is the
        highest level of detail, 1 is the next highest, and so on.

        If force is True, this will update every joint, even if we
        don't believe it's necessary.

        Returns True if any joint has changed as a result of this,
        False otherwise. """

        if lodName is None:
            lodNames = self.getLODNames()
        else:
            lodNames = [lodName]

        anyChanged = False
        if lod < len(lodNames):
            lodName = lodNames[lod]
            if partName is None:
                partBundleDict = self.__partBundleDict[lodName]
                partNames = list(partBundleDict.keys())
            else:
                partNames = [partName]

            for partName in partNames:
                partBundle = self.getPartBundle(partName, lodNames[lod])
                if force:
                    if partBundle.forceUpdate():
                        anyChanged = True
                else:
                    if partBundle.update():
                        anyChanged = True
        else:
            self.notify.warning('update() - no lod: %d' % lod)

        return anyChanged

    def setCenter(self, center):
        if center is None:
            center = Point3(0, 0, 0)
        self.__LODCenter = center
        if self.__LODNode:
            self.__LODNode.node().setCenter(self.__LODCenter)
        if self.__LODAnimation:
            self.setLODAnimation(*self.__LODAnimation)

    def __updateSortedLODNames(self):
        # Cache the sorted LOD names so we don't have to grab them
        # and sort them every time somebody asks for the list
        self.__sortedLODNames = list(self.__partBundleDict.keys())
        # Reverse sort the doing a string->int
        def sortKey(x):
            if not str(x).isdigit():
                smap = {'h':3,
                        'm':2,
                        'l':1,
                        'f':0}

                """
                sx = smap.get(x[0], None)

                if sx is None:
                    self.notify.error('Invalid lodName: %s' % x)
                """
                return smap[x[0]]
            else:
                return int(x)

        self.__sortedLODNames.sort(key=sortKey, reverse=True)

    def getLODNames(self):
        """
        Return list of Actor LOD names. If not an LOD actor,
        returns 'lodRoot'
        Caution - this returns a reference to the list - not your own copy
        """
        return self.__sortedLODNames

    def instance(self, path, partName, jointName, lodName="lodRoot"):
        """instance(self, NodePath, string, string, key="lodRoot")
        Instance a nodePath to an actor part at a joint called jointName"""
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named %s!" % (lodName))
            return None

        partDef = partBundleDict.get(partName)
        if not partDef:
            Actor.notify.warning("no part named %s!" % (partName))
            return None

        joint = partDef.charNP.find("**/" + jointName)
        if joint.isEmpty():
            Actor.notify.warning("%s not found!" % (jointName))
            return None

        return path.instanceTo(joint)

    def attach(self, partName, anotherPartName, jointName, lodName="lodRoot"):
        """attach(self, string, string, string, key="lodRoot")
        Attach one actor part to another at a joint called jointName"""
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named %s!" % (lodName))
            return

        partDef = partBundleDict.get(partName)
        if not partDef:
            Actor.notify.warning("no part named %s!" % (partName))
            return

        anotherPartDef = partBundleDict.get(anotherPartName)
        if not anotherPartDef:
            Actor.notify.warning("no part named %s!" % (anotherPartName))
            return

        joint = anotherPartDef.charNP.find("**/" + jointName)
        if joint.isEmpty():
            Actor.notify.warning("%s not found!" % (jointName))
            return

        partDef.charNP.reparentTo(joint)

    def drawInFront(self, frontPartName, backPartName, mode,
                    root=None, lodName=None):
        """drawInFront(self, string, int, string=None, key=None)

        Arrange geometry so the frontPart(s) are drawn in front of
        backPart.

        If mode == -1, the geometry is simply arranged to be drawn in
        the correct order, assuming it is already under a
        direct-render scene graph (like the DirectGui system).  That
        is, frontPart is reparented to backPart, and backPart is
        reordered to appear first among its siblings.

        If mode == -2, the geometry is arranged to be drawn in the
        correct order, and depth test/write is turned off for
        frontPart.

        If mode == -3, frontPart is drawn as a decal onto backPart.
        This assumes that frontPart is mostly coplanar with and does
        not extend beyond backPart, and that backPart is mostly flat
        (not self-occluding).

        If mode > 0, the frontPart geometry is placed in the 'fixed'
        bin, with the indicated drawing order.  This will cause it to
        be drawn after almost all other geometry.  In this case, the
        backPartName is actually unused.

        Takes an optional argument root as the start of the search for the
        given parts. Also takes optional lod name to refine search for the
        named parts. If root and lod are defined, we search for the given
        root under the given lod.
        """
        # check to see if we are working within an lod
        if lodName is not None:
            # find the named lod node
            lodRoot = self.__LODNode.find(str(lodName))
            if root is None:
                # no need to look further
                root = lodRoot
            else:
                # look for root under lod
                root = lodRoot.find("**/" + root)
        else:
            # start search from self if no root and no lod given
            if root is None:
                root = self

        frontParts = root.findAllMatches("**/" + frontPartName)

        if mode > 0:
            # Use the 'fixed' bin instead of reordering the scene
            # graph.
            for part in frontParts:
                part.setBin('fixed', mode)
            return

        if mode == -2:
            # Turn off depth test/write on the frontParts.
            for part in frontParts:
                part.setDepthWrite(0)
                part.setDepthTest(0)

        # Find the back part.
        backPart = root.find("**/" + backPartName)
        if backPart.isEmpty():
            Actor.notify.warning("no part named %s!" % (backPartName))
            return

        if mode == -3:
            # Draw as a decal.
            backPart.node().setEffect(DecalEffect.make())
        else:
            # Reorder the backPart to be the first of its siblings.
            backPart.reparentTo(backPart.getParent(), -1)

        #reparent all the front parts to the back part
        frontParts.reparentTo(backPart)

    def getPart(self, partName="modelRoot", lodName="lodRoot"):
        """
        Find the named part in the optional named lod and return it, or
        return None if not present
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return None
        partDef = partBundleDict.get(partName)
        if partDef is not None:
            return partDef.charNP
        return None

    def getPartModel(self, partName="modelRoot", lodName="lodRoot"):
        """
        Returns a NodePath to the ModelRoot of the indicated part name.
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            return NodePath()
        partDef = partBundleDict.get(partName)
        if not partDef:
            return NodePath()
        return partDef.partModel

    def getPartBundle(self, partName="modelRoot", lodName="lodRoot"):
        """
        Find the named part in the optional named lod and return its
        associated PartBundle, or return None if not present
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return None
        partDef = partBundleDict.get(partName)
        if partDef is not None:
            return partDef.char
        return None

    def removePart(self, partName="modelRoot", lodName="lodRoot"):
        """
        Remove the geometry and animations of the named part of the
        optional named lod if present.
        NOTE: this will remove child geometry also!
        """
        # find the corresponding part bundle dict
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return

        # remove the part
        if partName in partBundleDict:
            partDef = partBundleDict[partName]
            if not partDef.charNP.isEmpty():
                partDef.charNP.removeNode()
            if not partDef.partModel.isEmpty():
                partDef.partModel.removeNode()
            del partBundleDict[partName]

    def hidePart(self, partName, lodName="lodRoot"):
        """
        Make the given part of the optionally given lod not render,
        even though still in the tree.
        NOTE: this will affect child geometry
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return
        partDef = partBundleDict.get(partName)
        if partDef:
            partDef.charNP.hide()
        else:
            Actor.notify.warning("no part named %s!" % (partName))

    def showPart(self, partName, lodName="lodRoot"):
        """
        Make the given part render while in the tree.
        NOTE: this will affect child geometry
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return
        partDef = partBundleDict.get(partName)
        if partDef:
            partDef.charNP.show()
        else:
            Actor.notify.warning("no part named %s!" % (partName))

    def showAllParts(self, partName, lodName="lodRoot"):
        """
        Make the given part and all its children render while in the tree.
        NOTE: this will affect child geometry
        """
        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.warning("no lod named: %s" % (lodName))
            return
        partDef = partBundleDict.get(partName)
        if partDef:
            partDef.charNP.show()
            partDef.charNP.getChildren().show()
        else:
            Actor.notify.warning("no part named %s!" % (partName))

    def actorInterval(self, *args, **kw):
        from direct.interval import ActorInterval
        return ActorInterval.ActorInterval(self, *args, **kw)

    def cleanup(self):
        """
        This method should be called when intending to destroy the Actor, and
        cleans up any additional resources stored on the Actor class before
        removing the underlying node using `removeNode()`.

        Note that `removeNode()` itself is not sufficient to destroy actors,
        which is why this method exists.
        """
        self.stop(None)
        self.clearPythonData()
        self.flush()
        if(self.__geomNode):
            self.__geomNode.removeNode()
            self.__geomNode = None
        if not self.isEmpty():
            self.removeNode()

    def removeNode(self):
        """
        You should call `cleanup()` for Actor objects instead, since
        :meth:`~panda3d.core.NodePath.removeNode()` is not sufficient for
        completely destroying Actor objects.
        """
        if self.__geomNode and (self.__geomNode.getNumChildren() > 0):
            assert self.notify.warning("called actor.removeNode() on %s without calling cleanup()" % self.getName())
        NodePath.removeNode(self)

    def clearPythonData(self):
        self.__partBundleDict = {}
        self.__sortedLODNames = []
        #self.__animControlDict = {}

    def flush(self):
        """
        Actor flush function.  Used by `cleanup()`.
        """
        self.clearPythonData()

        if self.__LODNode and (not self.__LODNode.isEmpty()):
            self.__LODNode.removeNode()
            self.__LODNode = None

        # remove all its children
        if self.__geomNode:
            self.__geomNode.getChildren().detach()

        self.__hasLOD = 0

    def __cmp__(self, other):
        # Actor inherits from NodePath, which inherits a definition of
        # __cmp__ from FFIExternalObject that uses the NodePath's
        # compareTo() method to compare different NodePaths.  But we
        # don't want this behavior for Actors; Actors should only be
        # compared pointerwise.  A NodePath that happens to reference
        # the same node is still different from the Actor.
        if self is other:
            return 0
        else:
            return 1

    def delete(self):
        try:
            self.Actor_deleted
            return
        except:
            self.Actor_deleted = 1
            self.cleanup()

    def copyActor(self, other, overwrite=False):
        # act like a copy constructor
        self.gotName = other.gotName

        # copy the scene graph elements of other
        if overwrite:
            otherCopy = other.copyTo(NodePath())
            otherCopy.detachNode()
            # assign these elements to ourselve (overwrite)
            self.assign(otherCopy)
        else:
            # just copy these to ourselves
            otherCopy = other.copyTo(self)
        # masad: check if otherCopy has a geomNode as its first child
        # if actor is initialized with flattenable, then otherCopy, not
        # its first child, is the geom node; check __init__, for reference
        if other.getGeomNode().getName() == other.getName():
            self.setGeomNode(otherCopy)
        else:
            self.setGeomNode(otherCopy.getChild(0))

        # copy the switches for lods
        self.switches = other.switches
        self.__LODNode = self.find('**/+LODNode')
        self.__hasLOD = 0
        if not self.__LODNode.isEmpty():
            self.__hasLOD = 1


        # copy the part dictionary from other
        self.__copyPartBundles(other)

    def __copyPartBundles(self, other):
        """__copyPartBundles(self, Actor)
        Copy the part bundle dictionary from another actor as this
        instance's own. NOTE: this method does not actually copy geometry
        """
        for lodName in other.__partBundleDict:
            # find the lod Asad
            if lodName == 'lodRoot':
                partLod = self
            else:
                partLod = self.__LODNode.find(str(lodName))
            if partLod.isEmpty():
                Actor.notify.warning("no lod named: %s" % (lodName))
                return None
            for partName, partDef in other.__partBundleDict[lodName].items():

                # find the part in our tree
                bundleNP = partLod.find("**/%s%s"%(Actor.partPrefix,partName))
                if bundleNP is not None:
                    # store the part bundle
                    self.__prepareBundle(bundleNP, partDef.partModel,
                                         partName, lodName)
                    thisPartDef = self.__partBundleDict[lodName][partName]
                    thisPartDef.weightLists = dict(partDef.weightLists)
                    for animDef in partDef.animsByName.values():
                        animDef.makeCopy(thisPartDef)
                else:
                    Actor.notify.error("lod: %s has no matching part: %s" %
                                       (lodName, partName))

    def stop(self, animName=None, partName=None, layer=None, kill=False):
        """stop(self, string=None, string=None)
        Stop named animation on the given part of the actor.
        If no name specified then stop all animations on the actor.
        NOTE: stops all LODs"""

        if animName is not None:
            for partDef in self.getPartDefs(partName):
                channelIndex = partDef.getChannelIndex(animName)
                if channelIndex == -1:
                    continue
                for i in range(partDef.char.getNumAnimLayers()):
                    animLayer = partDef.char.getAnimLayer(i)
                    if animLayer._sequence == channelIndex:
                        # This layer is playing the channel we want to stop.
                        partDef.char.stop(i, kill)
        else:
            # Stopping all layers or a specific layer
            for partDef in self.getPartDefs(partName):
                if layer is None:
                    # Stopping all layers.
                    partDef.char.stop(-1, kill)
                elif layer < partDef.char.getNumAnimLayers():
                    partDef.char.stop(layer, kill)

    def play(self, animName=None, partName=None, fromFrame=None, toFrame=None, layer=0,
             playRate=1.0, autoKill=False, blendIn=0.0, blendOut=0.0, channel=None):
        """play(self, string, string=None)
        Play the given animation on the given part of the actor.
        If no part is specified, try to play on all parts. NOTE:
        plays over ALL LODs"""

        if animName is None and channel is None:
            return

        if fromFrame is None:
            fromFrame = 0

        if animName is not None:
            lookup = animName
        else:
            lookup = channel

        for animDef in self.getAnimDefs(lookup, partName):
            if toFrame is None:
                animDef.char.play(animDef.index, fromFrame, animDef.channel.getNumFrames() - 1,
                                  layer, animDef.playRate * playRate, autoKill, blendIn, blendOut)
            else:
                animDef.char.play(animDef.index, fromFrame, toFrame, layer,
                                  animDef.playRate * playRate, autoKill, blendIn, blendOut)

    def loop(self, animName=None, restart=1, partName=None,
             fromFrame=None, toFrame=None, layer=0,
             playRate=1.0, blendIn=0.0, channel=None):
        """loop(self, string, int=1, string=None)
        Loop the given animation on the given part of the actor,
        restarting at zero frame if requested. If no part name
        is given then try to loop on all parts. NOTE: loops on
        all LOD's
        """

        if animName is None and channel is None:
            return

        if fromFrame is None:
            fromFrame = 0

        if animName is not None:
            lookup = animName
        else:
            lookup = channel

        for animDef in self.getAnimDefs(lookup, partName):
            if toFrame is None:
                animDef.char.loop(animDef.index, restart, fromFrame, animDef.channel.getNumFrames() - 1,
                                  layer, animDef.playRate * playRate, blendIn)
            else:
                animDef.char.loop(animDef.index, restart, fromFrame, toFrame, layer,
                                  animDef.playRate * playRate, blendIn)

    def pingpong(self, animName=None, restart=1, partName=None,
                 fromFrame=None, toFrame=None, layer=0,
                 playRate=1.0, blendIn=0.0, channel=None):
        """pingpong(self, string, int=1, string=None)
        Loop the given animation on the given part of the actor,
        restarting at zero frame if requested. If no part name
        is given then try to loop on all parts. NOTE: loops on
        all LOD's"""

        assert animName is not None or channel is not None

        if fromFrame is None:
            fromFrame = 0

        if animName is not None:
            lookup = animName
        else:
            lookup = channel

        for animDef in self.getAnimDefs(lookup, partName):
            if toFrame is None:
                animDef.char.pingpong(animDef.index, restart, fromFrame,
                                      animDef.channel.getNumFrames() - 1,
                                      layer, animDef.playRate * playRate, blendIn)
            else:
                animDef.char.pingpong(animDef.index, restart, fromFrame, toFrame,
                                      layer, animDef.playRate * playRate, blendIn)

    def pose(self, animName, frame, partName=None, lodName=None,
             layer=0, blendIn=0.0, blendOut=0.0):
        """pose(self, string, int, string=None)
        Pose the actor in position found at given frame in the specified
        animation for the specified part. If no part is specified attempt
        to apply pose to all parts."""

        for animDef in self.getAnimDefs(animName, partName, lodName):
            animDef.char.pose(animDef.index, frame, layer, blendIn, blendOut)

    def setTransition(self, animName, flag, partName=None, lodName=None):
        """
        Enables or disables transitions into the indicated animation.
        """
        for animDef in self.getAnimDefs(animName, partName, lodName):
            if flag:
                animDef.channel.clearFlags(AnimChannel.FSnap)
            else:
                animDef.channel.setFlags(AnimChannel.FSnap)

    def getAnimDefs(self, animName, partName=None, lodName=None):
        """
        Returns a list of AnimDefs for each part and lod combination for
        the indicated animName (may also be a channel index).
        """

        animDefs = []
        if lodName is None:
            # All LODs.
            for lod in self.__partBundleDict.values():
                if partName is None:
                    # All parts.
                    for partDef in lod.values():
                        animDef = partDef.getAnimDef(animName)
                        if animDef:
                            if animDef.isBound():
                                animDefs.append(animDef)
                            elif self.loadAndBindAnim(partDef, animDef):
                                animDefs.append(animDef)
                else:
                    # A subset of parts.
                    if isinstance(partName, str):
                        partsToGet = [partName]
                    else:
                        partsToGet = partName

                    for partToGet in partsToGet:
                        partDef = lod[partToGet]
                        animDef = partDef.getAnimDef(animName)
                        if animDef:
                            if animDef.isBound():
                                animDefs.append(animDef)
                            elif self.loadAndBindAnim(partDef, animDef):
                                animDefs.append(animDef)
        else:
            if not self.__partBundleDict:
                return []

            lod = self.__partBundleDict[lodName]
            if partName is None:
                # All parts.
                for partDef in lod.values():
                    animDef = partDef.getAnimDef(animName)
                    if animDef:
                        if animDef.isBound():
                            animDefs.append(animDef)
                        elif self.loadAndBindAnim(partDef, animDef):
                            animDefs.append(animDef)
            else:
                # A subset of parts.
                if isinstance(partName, str):
                    partsToGet = [partName]
                else:
                    partsToGet = partName

                for partToGet in partsToGet:
                    partDef = lod[partToGet]
                    animDef = partDef.getAnimDef(animName)
                    if animDef:
                        if animDef.isBound():
                            animDefs.append(animDef)
                        elif self.loadAndBindAnim(partDef, animDef):
                            animDefs.append(animDef)

        return animDefs

    def getPartDefs(self, partName=None, lodName=None):
        """
        Returns a list of PartDefs for each part and lod combination.
        """

        partDefs = []
        if lodName is None:
            # All LODs.
            for lod in self.__partBundleDict.values():
                if partName is None:
                    # All parts.
                    for partDef in lod.values():
                        partDefs.append(partDef)
                else:
                    # A subset of parts.
                    if isinstance(partName, str):
                        partsToGet = [partName]
                    else:
                        partsToGet = partName

                    for partToGet in partsToGet:
                        partDef = lod[partToGet]
                        partDefs.append(partDef)
        else:
            if not self.__partBundleDict:
                return []

            lod = self.__partBundleDict[lodName]
            if partName is None:
                # All parts.
                for partDef in lod.values():
                    partDefs.append(partDef)
            else:
                # A subset of parts.
                if isinstance(partName, str):
                    partsToGet = [partName]
                else:
                    partsToGet = partName

                for partToGet in partsToGet:
                    partDef = lod[partToGet]
                    partDefs.append(partDef)

        return partDefs

    def getCurrentAnim(self, partName=None, layer=0):
        """
        Return the anim currently playing on the actor. If part not
        specified return current anim of an arbitrary part in dictionary.
        NOTE: only returns info for an arbitrary LOD
        """

        if not self.__partBundleDict:
            return None

        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        if partName is None:
            partName, partDef = next(iter(partBundleDict.items()))
        else:
            partDef = partBundleDict.get(partName)
            if not partDef:
                # Part was not present.
                Actor.notify.warning("couldn't find part: %s" % (partName))
                return None

        # Return the animation playing on the indicated layer of the part.
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return None

        if not animLayer.isPlaying():
            return None

        # Return the name associated with the channel index the layer is
        # playing.
        animDef = partDef.animsByIndex.get(animLayer._sequence)
        if animDef:
            return animDef.name
        else:
            return None

    def getCurrentChannel(self, partName="modelRoot", layer=0):
        """
        Returns the index of the currently playing channel on the indicated
        layer of the indicated part.
        """

        if not self.__partBundleDict:
            return -1

        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return -1
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return -1
        return animLayer._sequence

    def getChannelLength(self, channel, partName="modelRoot"):
        if not self.__partBundleDict:
            return 0
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return 0
        chan = partDef.char.getChannel(channel)
        if not chan:
            return 0
        return chan.getLength(partDef.char)

    def getChannelActivity(self, channel, partName="modelRoot", index=0):
        if not self.__partBundleDict:
            return -1
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return -1
        chan = partDef.char.getChannel(channel)
        if not chan:
            return -1
        if chan.getNumActivities() == 0:
            return -1
        return chan.getActivity(index)

    def getChannelForActivity(self, activity, partName="modelRoot", seed=0, layer=0):
        """
        Returns a channel index for the indicated activity on the indicated
        part.
        """
        if not self.__partBundleDict:
            return -1
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return -1
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            currChannel = -1
        else:
            currChannel = animLayer._sequence
        return partDef.char.getChannelForActivity(activity, currChannel, seed)

    def getCurrentActivity(self, partName="modelRoot", layer=0):
        """
        Returns the current activity number of the indicated layer.
        """

        if not self.__partBundleDict:
            return -1
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return -1
        if layer < 0 or layer >= partDef.char.getNumAnimLayers():
            return -1
        return partDef.char.getAnimLayer(layer)._activity

    def isCurrentChannelFinished(self, partName="modelRoot", layer=0):
        """
        Returns true if the channel playing on the indicated layer of the
        indicated part has finished playing.
        """
        if not self.__partBundleDict:
            return True
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return True
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return True
        return animLayer._sequence_finished

    def isChannelPlaying(self, partName="modelRoot", layer=0):
        """
        Returns true if the indicated layer of the indicated part is currently
        playing a channel.
        """
        if not self.__partBundleDict:
            return False
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return False
        if layer < 0 or layer >= partDef.char.getNumAnimLayers():
            return False
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return False
        return animLayer.isPlaying()

    def getCycle(self, partName="modelRoot", layer=0):
        """
        Returns the current cycle of the channel playing on the indicated layer
        of the indicated part.
        """
        if not self.__partBundleDict:
            return 0.0
        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict.get(partName)
        if not partDef:
            return 0.0
        animLayer = partDef.char.getAnimLayer(layer)
        if not animLayer:
            return 0.0
        return animLayer._cycle

    def getCurrentFrame(self, animName=None, partName=None, layer=0):
        """
        Return the current frame number of the named anim, or if no
        anim is specified, then the anim current playing on the
        actor. If part not specified return current anim of first part
        in dictionary.  NOTE: only returns info for an arbitrary LOD
        """

        if not self.__partBundleDict:
            return 0

        if animName is None:
            # Return current frame of layer.
            lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
            if partName is None:
                partName, partDef = next(iter(partBundleDict.items()))
            else:
                partDef = partBundleDict.get(partName)
                if not partDef:
                    # Part was not present.
                    Actor.notify.warning("couldn't find part: %s" % (partName))
                    return 0

            # Return the animation playing on the indicated layer of the part.
            animLayer = partDef.char.getAnimLayer(layer)
            if not animLayer:
                return 0

            if not animLayer.isPlaying():
                return 0

            chan = partDef.char.getChannel(animLayer._sequence)
            return int(animLayer._cycle * (chan.getNumFrames() - 1))
        else:
            # Return current frame of the named animation if it is currently
            # playing on any layer.
            animDefs = self.getAnimDefs(animName, partName)
            if not animDefs:
                return 0
            animDef = animDefs[0]
            # Find the layer playing the channel.
            for i in range(animDef.char.getNumAnimLayers()):
                animLayer = animDef.char.getAnimLayer(i)
                if animLayer._sequence == animDef.index and animLayer.isPlaying():
                    return int(animLayer._cycle * (animDef.channel.getNumFrames() - 1))

        return 0

    # these functions compensate for actors that are modeled facing the viewer but need
    # to face away from the camera in the game
    def faceAwayFromViewer(self):
        self.getGeomNode().setH(180)
    def faceTowardsViewer(self):
        self.getGeomNode().setH(0)

    def advance(self, partName=None):
        """
        Advances the animation time on all layers of the indicated part, or all
        parts if partName is None.
        """
        for bundle in self.getPartBundles(partName):
            bundle.advance()

    def setAutoAdvance(self, flag, partName = None):
        for bundle in self.getPartBundles(partName):
            bundle.setAutoAdvanceFlag(flag)

    def setBlend(self, animBlend = None, frameBlend = None,
                 blendType = None, partName = None, transitionBlend = None):
        """
        Changes the way the Actor handles blending of multiple
        different animations, and/or interpolation between consecutive
        frames.

        The animBlend and frameBlend parameters are boolean flags.
        You may set either or both to True or False.  If you do not
        specify them, they do not change from the previous value.

        When animBlend is True, multiple different animations may
        simultaneously be playing on the Actor.  This means you may
        call play(), loop(), or pose() on multiple animations and have
        all of them contribute to the final pose each frame.

        In this mode (that is, when animBlend is True), starting a
        particular animation with play(), loop(), or pose() does not
        implicitly make the animation visible; you must also call
        setControlEffect() for each animation you wish to use to
        indicate how much each animation contributes to the final
        pose.

        The frameBlend flag is unrelated to playing multiple
        animations.  It controls whether the Actor smoothly
        interpolates between consecutive frames of its animation (when
        the flag is True) or holds each frame until the next one is
        ready (when the flag is False).  The default value of
        frameBlend is controlled by the interpolate-frames Config.prc
        variable.

        In either case, you may also specify blendType, which controls
        the precise algorithm used to blend two or more different
        matrix values into a final result.  Different skeleton
        hierarchies may benefit from different algorithms.  The
        default blendType is controlled by the anim-blend-type
        Config.prc variable.
        """
        for bundle in self.getPartBundles(partName = partName):
            #if blendType is not None:
            #    bundle.setBlendType(blendType)
            #if animBlend is not None:
            #    bundle.setAnimBlendFlag(animBlend)
            if frameBlend is not None:
                bundle.setFrameBlendFlag(frameBlend)
            if transitionBlend is not None:
                bundle.setChannelTransitionFlag(transitionBlend)

    def enableBlend(self, blendType = None, partName = None):
        """
        Enables blending of multiple animations simultaneously.
        After this is called, you may call play(), loop(), or pose()
        on multiple animations and have all of them contribute to the
        final pose each frame.

        With blending in effect, starting a particular animation with
        play(), loop(), or pose() does not implicitly make the
        animation visible; you must also call setControlEffect() for
        each animation you wish to use to indicate how much each
        animation contributes to the final pose.

        This method is deprecated.  You should use setBlend() instead.
        """
        self.setBlend(animBlend = True, blendType = blendType, partName = partName)

    def disableBlend(self, partName = None):
        """
        Restores normal one-animation-at-a-time operation after a
        previous call to enableBlend().

        This method is deprecated.  You should use setBlend() instead.
        """
        self.setBlend(animBlend = False, partName = partName)

    def getPartBundles(self, partName = None):
        """ Returns a list of PartBundle objects for the entire Actor,
        or for the indicated part only. """

        bundles = []

        for lodName, partBundleDict in self.__partBundleDict.items():
            if partName is None:
                for partDef in partBundleDict.values():
                    bundles.append(partDef.char)

            else:
                partDef = partBundleDict.get(partName)
                if partDef is not None:
                    bundles.append(partDef.char)
                else:
                    Actor.notify.warning("Couldn't find part: %s" % (partName))

        return bundles

    def getPartBundleDict(self):
        return self.__partBundleDict

    def listJoints(self, partName="modelRoot", lodName="lodRoot"):
        """Handy utility function to list the joint hierarchy of the
        actor. """

        partBundleDict = self.__partBundleDict.get(lodName)
        if not partBundleDict:
            Actor.notify.error("no lod named: %s" % (lodName))

        partDef = partBundleDict.get(partName)
        if partDef is None:
            Actor.notify.error("no part named: %s" % (partName))

        self.__doListJoints(0, partDef.char, 0)

    def __doListJoints(self, indentLevel, char, joint):
        name = char.getJointName(joint)
        val = char.getJointValue(joint)
        print(' '.join((' ' * indentLevel, name, str(TransformState.makeMat(val)))))

        for i in range(char.getJointNumChildren(joint)):
            self.__doListJoints(indentLevel + 2, char, char.getJointChild(joint, i))

    def getAnimFilename(self, animName, partName='modelRoot'):
        """
        Returns the filename that the channel with the indicated name was
        loaded from.  This returns None for channels that were embedded in
        the model.

        Returns the filename for an arbitrary LOD.
        """

        if not self.__partBundleDict:
            return None

        lodName, partBundleDict = next(iter(self.__partBundleDict.items()))
        partDef = partBundleDict[partName]
        animDef = partDef.getAnimDef(animName)
        if not animDef:
            return None
        return animDef.filename

    def postFlatten(self):
        """
        No-op.
        """
        pass

    def controlJoint(self, node, partName, jointName, lodName="lodRoot"):
        """The converse of exposeJoint: this associates the joint with
        the indicated node, so that the joint transform will be copied
        from the node to the joint each frame.  This can be used for
        programmer animation of a particular joint at runtime.

        The parameter node should be the NodePath for the node whose
        transform will animate the joint.  If node is None, a new node
        will automatically be created and loaded with the joint's
        initial transform.  In either case, the node used will be
        returned.

        It used to be necessary to call this before any animations
        have been loaded and bound, but that is no longer so.
        """
        anyGood = False
        for bundleDict in self.__partBundleDict.values():
            char = bundleDict[partName].char

            joint = char.findJoint(jointName)

            if node is None:
                node = self.attachNewNode(ModelNode(jointName))
                if joint != -1:
                    node.setMat(char.getJointDefaultValue(joint))

            if joint != -1:
                char.setJointControllerNode(joint, node.node())
                anyGood = True

        if not anyGood:
            self.notify.warning("Cannot control joint %s" % (jointName))

        return node

    def releaseJoint(self, partName, jointName):
        """Undoes a previous call to controlJoint() or freezeJoint()
        and restores the named joint to its normal animation. """

        for bundleDict in self.__partBundleDict.values():
            char = bundleDict[partName].char
            joint = char.findJoint(jointName)
            if joint == -1:
                continue
            char.clearJointControllerNode(joint)

    def getActorInfo(self):
        """
        Utility function to create a list of information about an actor.
        Useful for iterating over details of an actor.
        """

        lodInfo = []
        for lodName, partDict in self.__partBundleDict.items():
            partInfo = []
            for partName, partDef in partDict.items():
                char = partDef.char
                animDict = partDef.animsByName
                animInfo = []
                for animName, animDef in animDict.items():
                    file = animDef.filename
                    index = animDef.index
                    animInfo.append([animName, file, index, animDef])
                partInfo.append([partName, char, animInfo])
            lodInfo.append([lodName, partInfo])
        return lodInfo

    def getAnimNames(self):
        animNames = []
        for lodName, lodInfo in self.getActorInfo():
            for partName, char, animInfo in lodInfo:
                for animName, file, index, animDef in animInfo:
                    if animName not in animNames:
                        animNames.append(animName)
        return animNames

    def pprint(self):
        """
        Pretty print actor's details.
        """
        for lodName, lodInfo in self.getActorInfo():
            print('LOD: %s' % lodName)
            for partName, char, animInfo in lodInfo:
                print('  Part: %s' % partName)
                print('  Char: %r' % char)
                for animName, file, index, animDef in animInfo:
                    print('    Anim: %s' % animName)
                    print('      File: %s' % file)
                    if index < 0 or animDef.channel is None:
                        print(' (not loaded)')
                    else:
                        channel = animDef.channel
                        print('      Index: %i NumFrames: %d PlayRate: %0.2f' %
                              (index, channel.getNumFrames(), animDef.playRate))

