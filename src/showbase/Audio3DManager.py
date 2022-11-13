"""Contains the Audio3DManager class."""

__all__ = ['Audio3DManager']

from panda3d.core import Vec3, Point3, Quat, WeakNodePath, ClockObject, SteamAudioProperties
from direct.task.TaskManagerGlobal import Task, taskMgr

class Audio3DManager:

    def __init__(self, audio_manager, listener_target = None, root = None,
                 taskPriority = 49):
        self.audio_manager = audio_manager
        self.listener_target = listener_target

        if root is None:
            self.root = base.render
        else:
            self.root = root

        self.sound_dict = {}
        self.vel_dict = {}
        self.listener_vel = Vec3(0, 0, 0)

        taskMgr.add(self.update, "Audio3DManager-updateTask", taskPriority)

    def loadSfx(self, name, audioProperties=SteamAudioProperties(), stream=False):
        """
        Use Audio3DManager.loadSfx to load a sound with 3D positioning enabled
        """
        if not name:
            return None
        
        sound = self.audio_manager.getSound(name, 1, stream)
        sound.applySteamAudioProperties(audioProperties)
        return sound
        
    def applySteamAudioProperties(self, sound, audioProperties):
        """ 
        Apply the SteamAudioProperties to the sound in question. 
        """
        sound.applySteamAudioProperties(audioProperties)

    def setSoundMinDistance(self, sound, dist):
        """
        Controls the distance (in units) that this sound begins to fall off.
        Also affects the rate it falls off.
        Default is 3.28 (in feet, this is 1 meter)
        Don't forget to change this when you change the DistanceFactor
        """
        sound.set3dMinDistance(dist)

    def getSoundMinDistance(self, sound):
        """
        Controls the distance (in units) that this sound begins to fall off.
        Also affects the rate it falls off.
        Default is 3.28 (in feet, this is 1 meter)
        """
        return sound.get3dMinDistance()

    def setSoundMaxDistance(self, sound, dist):
        """
        Controls the maximum distance (in units) that this sound stops falling off.
        The sound does not stop at that point, it just doesn't get any quieter.
        You should rarely need to adjust this.
        Default is 1000000000.0
        """
        sound.set3dMaxDistance(dist)

    def getSoundMaxDistance(self, sound):
        """
        Controls the maximum distance (in units) that this sound stops falling off.
        The sound does not stop at that point, it just doesn't get any quieter.
        You should rarely need to adjust this.
        Default is 1000000000.0
        """
        return sound.get3dMaxDistance()

    def setSoundVelocity(self, sound, velocity):
        """
        Set the velocity vector (in units/sec) of the sound, for calculating doppler shift.
        This is relative to the sound root (probably render).
        Default: Vec3(0, 0, 0)
        """
        if isinstance(velocity, tuple) and len(velocity) == 3:
            velocity = Vec3(*velocity)
        if not isinstance(velocity, Vec3):
            raise TypeError("Invalid argument 1, expected <Vec3>")
        self.vel_dict[sound] = velocity

    def setSoundVelocityAuto(self, sound):
        """
        If velocity is set to auto, the velocity will be determined by the
        previous position of the object the sound is attached to and the frame dt.
        Make sure if you use this method that you remember to clear the previous
        transformation between frames.
        """
        self.vel_dict[sound] = None

    def getSoundVelocity(self, sound):
        """
        Get the velocity of the sound.
        """
        if sound in self.vel_dict:
            vel = self.vel_dict[sound]
            if vel is not None:
                return vel

            for known_object in list(self.sound_dict.keys()):
                if self.sound_dict[known_object].count(sound):
                    node_path = known_object.getNodePath()
                    if not node_path:
                        # The node has been deleted.
                        del self.sound_dict[known_object]
                        continue

                    clock = ClockObject.getGlobalClock()
                    return node_path.getPosDelta(self.root) / clock.getDt()

        return Vec3(0, 0, 0)

    def setListenerVelocity(self, velocity):
        """
        Set the velocity vector (in units/sec) of the listener, for calculating doppler shift.
        This is relative to the sound root (probably render).
        Default: Vec3(0, 0, 0)
        """
        if isinstance(velocity, tuple) and len(velocity) == 3:
            velocity = Vec3(*velocity)
        if not isinstance(velocity, Vec3):
            raise TypeError("Invalid argument 0, expected <Vec3>")
        self.listener_vel = velocity

    def setListenerVelocityAuto(self):
        """
        If velocity is set to auto, the velocity will be determined by the
        previous position of the object the listener is attached to and the frame dt.
        Make sure if you use this method that you remember to clear the previous
        transformation between frames.
        """
        self.listener_vel = None

    def getListenerVelocity(self):
        """
        Get the velocity of the listener.
        """
        if self.listener_vel is not None:
            return self.listener_vel
        elif self.listener_target is not None:
            clock = ClockObject.getGlobalClock()
            return self.listener_target.getPosDelta(self.root) / clock.getDt()

        return Vec3(0, 0, 0)

    def attachSoundToObject(self, sound, object):
        """
        Sound will come from the location of the object it is attached to.
        If the object is deleted, the sound will automatically be removed.
        """
        # sound is an AudioSound
        # object is any Panda object with coordinates
        for known_object in list(self.sound_dict.keys()):
            if self.sound_dict[known_object].count(sound):
                # This sound is already attached to something
                #return 0
                # detach sound
                self.sound_dict[known_object].remove(sound)
                if len(self.sound_dict[known_object]) == 0:
                    # if there are no other sounds, don't track
                    # the object any more
                    del self.sound_dict[known_object]

        if object not in self.sound_dict:
            self.sound_dict[WeakNodePath(object)] = []

        self.sound_dict[object].append(sound)

        # Apply the current object's position, orientation, and velocity to the sound immediately.
        pos = object.getPos(self.root)
        q = object.getQuat(self.root)
        vel = self.getSoundVelocity(sound)
        sound.set3dAttributes(pos, q, vel)

        return 1

    def detachSound(self, sound):
        """
        sound will no longer have it's 3D position updated
        """
        for known_object in list(self.sound_dict.keys()):
            if self.sound_dict[known_object].count(sound):
                self.sound_dict[known_object].remove(sound)
                if len(self.sound_dict[known_object]) == 0:
                    # if there are no other sounds, don't track
                    # the object any more
                    del self.sound_dict[known_object]
                return 1
        return 0

    def getSoundsOnObject(self, object):
        """
        returns a list of sounds attached to an object
        """
        if object not in self.sound_dict:
            return []
        sound_list = []
        sound_list.extend(self.sound_dict[object])
        return sound_list

    def attachListener(self, object):
        """
        Sounds will be heard relative to this object. Should probably be the camera.
        """
        self.listener_target = object
        return 1

    def detachListener(self):
        """
        Sounds will be heard relative to the root, probably render.
        """
        self.listener_target = None
        return 1

    def update(self, task=None):
        """
        Updates position of sounds in the 3D audio system. Will be called automatically
        in a task.
        """
        # Update the positions of all sounds based on the objects
        # to which they are attached

        # The audio manager is not active so do nothing
        if hasattr(self.audio_manager, "getActive"):
            if self.audio_manager.getActive() == 0:
                return Task.cont

        for known_object, sounds in list(self.sound_dict.items()):
            node_path = known_object.getNodePath()
            if not node_path:
                # The node has been deleted.
                del self.sound_dict[known_object]
                continue

            pos = node_path.getPos(self.root)
            q = node_path.getQuat(self.root)

            for sound in sounds:
                vel = self.getSoundVelocity(sound)
                sound.set3dAttributes(pos, q, vel)

        # Update the position of the listener based on the object
        # to which it is attached
        if self.listener_target:
            pos = self.listener_target.getPos(self.root)
            q = self.listener_target.getQuat(self.root)
            vel = self.getListenerVelocity()
            base.audioEngine.set3dListenerAttributes(pos, q, vel)
        else:
            base.audioEngine.set3dListenerAttributes(Point3(0, 0, 0), Quat(0, 0, 0, 0), Vec3(0, 0, 0))
        return Task.cont

    def disable(self):
        """
        Detaches any existing sounds and removes the update task
        """
        taskMgr.remove("Audio3DManager-updateTask")
        self.detachListener()
        for object in list(self.sound_dict.keys()):
            for sound in self.sound_dict[object]:
                self.detachSound(sound)