from DirectGuiGlobals import *
from DirectFrame import *
from DirectButton import *

def findDialog(uniqueName):
    """findPanel(string uniqueName)
    
    Returns the panel whose uniqueName is given.  This is mainly
    useful for debugging, to get a pointer to the current onscreen
    panel of a particular type.

    """
    if DirectDialog.AllDialogs.has_key(uniqueName):
        return DirectDialog.AllDialogs[uniqueName]
    return None

def cleanupDialog(uniqueName):
    """cleanupPanel(string uniqueName)

    Cleans up (removes) the panel with the given uniqueName.  This
    may be useful when some panels know about each other and know
    that opening panel A should automatically close panel B, for
    instance.
    """
        
    if DirectDialog.AllDialogs.has_key(uniqueName):
        # calling cleanup() will remove it out of the AllDialogs dict
        # This way it will get removed from the dict even it we did
        # not clean it up using this interface (ie somebody called
        # self.cleanup() directly
        DirectDialog.AllDialogs[uniqueName].cleanup()

class DirectDialog(DirectFrame):

    AllDialogs = {}
    PanelIndex = 0

    def __init__(self, parent = aspect2d, **kw):
        """
        DirectDialog(kw)

        Creates a popup dialog to alert and/or interact with user.
        Some of the main keywords that can be used to customize the dialog:
            Keyword              Definition
            -------              ----------
            text                 Text message/query displayed to user
            geom                 Geometry to be displayed in dialog
            buttonTextList       List of text to show on each button
            buttonGeomList       List of geometry to show on each button
            buttonImageList      List of images to show on each button
            buttonValueList      List of values sent to dialog command for
                                 each button.  If value is [] then the
                                 ordinal rank of the button is used as 
                                 its value
            buttonHotKeyList     List of hotkeys to bind to each button.
                                 Typing hotkey is equivalent to pressing
                                 the corresponding button.
            suppressKeys         Set to true if you wish to suppress keys
                                 (i.e. Dialog eats key event), false if
                                 you wish Dialog to pass along key event
            buttonSize           4-tuple used to specify custom size for
                                 each button (to make bigger then geom/text
                                 for example)
            pad                  Space between border and interior graphics
            topPad               Extra space added above text/geom/image
            midPad               Extra space added between text/buttons
            sidePad              Extra space added to either side of
                                 text/buttons
            buttonPadSF          Scale factor used to expand/contract 
                                 button horizontal spacing
            command              Callback command used when a button is
                                 pressed.  Value supplied to command
                                 depends on values in buttonValueList

         Note: Number of buttons on the dialog depends upon the maximum
               length of any button[Text|Geom|Image|Value]List specified.
               Values of None are substituted for lists that are shorter
               than the max length
         """
            
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('dialogName',        None,          INITOPT),
            # Default position is slightly forward in Y, so as not to
            # intersect the near plane, which is incorrectly set to 0
            # in DX for some reason.
            ('pos',               (0, 0.1, 0),   None),
            ('pad',               (0.1, 0.1),    None),
            ('text',              '',            None),
            ('text_align',        TextNode.ALeft,   None),
            ('text_scale',        0.06,          None),
            ('image',  getDefaultDialogGeom(),   None),
            ('relief',            None,          None),
            ('buttonTextList',    [],            INITOPT),
            ('buttonGeomList',    [],            INITOPT),
            ('buttonImageList',   [],            INITOPT),
            ('buttonValueList',   [],            INITOPT),
            ('buttonHotKeyList',  [],            INITOPT),
            ('button_borderWidth',(.01,.01),     None),
            ('button_pad',        (.01,.01),     None),
            ('button_relief',     RAISED,        None),
            ('button_text_scale'  , 0.06,        None),
            ('buttonSize',        None,          INITOPT),
            ('topPad',            0.06,          INITOPT),
            ('midPad',            0.12,          INITOPT),
            ('sidePad',           0.,            INITOPT),
            ('buttonPadSF',       1.05,          INITOPT),
            # Alpha of fade screen behind dialog
            ('fadeScreen',        0,             None),
            ('command',           None,          None),
            ('extraArgs',         [],            None),
            ('sortOrder',    NO_FADE_SORT_INDEX, None),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs, dynamicGroups = ("button",))

        # Initialize superclasses
        DirectFrame.__init__(self, parent)

        if not self['dialogName']:
            self['dialogName'] = 'DirectDialog_' + `DirectDialog.PanelIndex`
        # Clean up any previously existing panel with the same unique
        # name.  We don't allow any two panels with the same name to
        # coexist.
        cleanupDialog(self['dialogName'])
        # Store this panel in our map of all open panels.
        DirectDialog.AllDialogs[self['dialogName']] = self
        DirectDialog.PanelIndex += 1
        
        # Determine number of buttons
        self.numButtons = max(len(self['buttonTextList']),
                              len(self['buttonGeomList']),
                              len(self['buttonImageList']),
                              len(self['buttonValueList']))
        # Create buttons
        self.buttonList = []
        index = 0
        for i in range(self.numButtons):
            name = 'Button' + `i`
            try:
                text = self['buttonTextList'][i]
            except IndexError:
                text = None
            try:
                geom = self['buttonGeomList'][i]
            except IndexError:
                geom = None
            try:
                image = self['buttonImageList'][i]
            except IndexError:
                image = None
            try:
                value = self['buttonValueList'][i]
            except IndexError:
                value = i
                self['buttonValueList'].append(i)
            try:
                hotKey = self['buttonHotKeyList'][i]
            except IndexError:
                hotKey = None
            button = self.createcomponent(
                name, (), "button",
                DirectButton, (self,),
                text = text,
                geom = geom,
                image = image,
                suppressKeys = self['suppressKeys'],
                frameSize = self['buttonSize'],
                command = lambda s = self, v = value: s.buttonCommand(v)
                )
            self.buttonList.append(button)

        # Update dialog when everything has been initialised
        self.postInitialiseFuncList.append(self.configureDialog)
        self.initialiseoptions(DirectDialog)

    def configureDialog(self):
        # Set up hot key bindings
        bindList = zip(self.buttonList, self['buttonHotKeyList'],
                       self['buttonValueList'])
        for button, hotKey, value in bindList:
            if ((type(hotKey) == types.ListType) or
                (type(hotKey) == types.TupleType)):
                for key in hotKey:
                    button.bind('press-' + key + '-', self.buttonCommand,
                                extraArgs = [value])
                    self.bind('press-' + key + '-', self.buttonCommand,
                              extraArgs = [value])
                    
            else:
                button.bind('press-' + hotKey + '-',self.buttonCommand,
                            extraArgs = [value])
                self.bind('press-' + hotKey + '-', self.buttonCommand,
                          extraArgs = [value])
        # Position buttons and text
        pad = self['pad']
        image = self.component('image0')
        # Get size of text/geom without image (for state 0)
        if image:
            image.reparentTo(hidden)
        bounds = self.stateNodePath[0].getTightBounds()
        if image:
            image.reparentTo(self.stateNodePath[0])
        l = bounds[0][0]
        r = bounds[1][0]
        b = bounds[0][2]
        t = bounds[1][2]
        # Center text and geom around origin
        # How far is center of text from origin?
        xOffset = -(l+r)*0.5
        zOffset = -(b+t)*0.5
        # Update bounds to reflect text movement
        l += xOffset
        r += xOffset
        b += zOffset
        t += zOffset
        # Offset text and geom to center
        if self['text']:
            self['text_pos'] = (self['text_pos'][0] + xOffset,
                                self['text_pos'][1] + zOffset)
        if self['geom']:
            self['geom_pos'] = Point3(self['geom_pos'][0] + xOffset,
                                      self['geom_pos'][1],
                                      self['geom_pos'][2] + zOffset)
        if self.numButtons != 0:
            bpad = self['button_pad']
            # Get button size
            if self['buttonSize']:
                # Either use given size
                buttonSize = self['buttonSize']
                bl = buttonSize[0]
                br = buttonSize[1]
                bb = buttonSize[2]
                bt = buttonSize[3]
            else:
                # Or get bounds of union of buttons
                bl = br = bb = bt = 0
                for button in self.buttonList:
                    bounds = button.stateNodePath[0].getTightBounds()
                    bl = min(bl, bounds[0][0])
                    br = max(br, bounds[1][0])
                    bb = min(bb, bounds[0][2])
                    bt = max(bt, bounds[1][2])
                bl -= bpad[0]
                br += bpad[0]
                bb -= bpad[1]
                bt += bpad[1]
                # Now resize buttons to match largest
                for button in self.buttonList:
                    button['frameSize'] = (bl,br,bb,bt)
            # Must compensate for scale
            scale = self['button_scale']
            # Can either be a Vec3 or a tuple of 3 values
            if (isinstance(scale, Vec3) or
                (type(scale) == types.ListType) or
                (type(scale) == types.TupleType)):
                sx = scale[0]
                sz = scale[2]
            elif ((type(scale) == types.IntType) or
                  (type(scale) == types.FloatType)):
                sx = sz = scale
            else:
                sx = sz = 1
            bl *= sx
            br *= sx
            bb *= sz
            bt *= sz
            # Position buttons
            # Calc button width and height
            bHeight = bt - bb
            bWidth = br - bl
            # Add pad between buttons
            bSpacing = self['buttonPadSF'] * bWidth
            bPos = -bSpacing * (self.numButtons - 1)*0.5
            index = 0
            for button in self.buttonList:
                button.setPos(bPos + index * bSpacing, 0,
                              b - self['midPad'] - bpad[1] - bt)
                index += 1
            bMax = bPos + bSpacing * (self.numButtons - 1)
        else:
            bpad = 0
            bl = br = bb = bt = 0
            bPos = 0
            bMax = 0
            bpad = (0,0)
            bHeight = bWidth = 0
        # Resize frame to fit text and buttons
        l = min(bPos + bl, l) - pad[0]
        r = max(bMax + br, r) + pad[0]
        sidePad = self['sidePad']
        l -= sidePad
        r += sidePad
        # reduce bottom by pad, button height and 2*button pad
        b = min(b - self['midPad'] - bpad[1] - bHeight - bpad[1], b) - pad[1]
        t = t + self['topPad'] + pad[1]
        self['image_scale'] = (r - l, 1, t - b)
        # Center frame about text and buttons
        self['image_pos'] = ((l+r)*0.5, 0.0,(b+t)*0.5)
        self.resetFrameSize()

    def show(self):
        """show(self)
        """
        if self['fadeScreen']:
            base.transitions.fadeScreen(self['fadeScreen'])
        NodePath.show(self)

    def hide(self):
        """hide(self)
        """
        if self['fadeScreen']:
            base.transitions.noTransitions()
        NodePath.hide(self)

    def buttonCommand(self, value, event = None):
        if self['command']:
            self['command'](value)

    def setMessage(self, message):
        self['text'] = message
        self.configureDialog()
        
    def cleanup(self):
        """unload(self)
        """
        # Remove this panel out of the AllDialogs list
        uniqueName = self['dialogName']
        if DirectDialog.AllDialogs.has_key(uniqueName):
            del DirectDialog.AllDialogs[uniqueName]
        self.destroy()

    def destroy(self):
        if self['fadeScreen']:
            base.transitions.noTransitions()
        DirectFrame.destroy(self)

class OkDialog(DirectDialog):
    def __init__(self, parent = aspect2d, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  ['OK'],       INITOPT),
            ('buttonValueList', [DIALOG_OK],          INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(OkDialog)

class OkCancelDialog(DirectDialog):
    def __init__(self, parent = aspect2d, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  ['OK','Cancel'],       INITOPT),
            ('buttonValueList', [DIALOG_OK,DIALOG_CANCEL], INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(OkCancelDialog)

class YesNoDialog(DirectDialog):
    def __init__(self, parent = aspect2d, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  ['Yes', 'No'],       INITOPT),
            ('buttonValueList', [DIALOG_YES,DIALOG_NO], INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(YesNoDialog)

class YesNoCancelDialog(DirectDialog):
    def __init__(self, parent = aspect2d, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  ['Yes', 'No', 'Cancel'],  INITOPT),
            ('buttonValueList', [DIALOG_YES,DIALOG_NO,DIALOG_CANCEL],
             INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(YesNoCancelDialog)

class RetryCancelDialog(DirectDialog):
    def __init__(self, parent = aspect2d, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  ['Retry','Cancel'],   INITOPT),
            ('buttonValueList', [DIALOG_RETRY,DIALOG_CANCEL], INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(RetryCancelDialog)

