"""Instantiates the global :class:`~.Messenger.Messenger` object."""

__all__ = ['messenger']


'''
from panda3d.direct import Messenger

#: Contains the global :class:`~.Messenger.Messenger` instance.
messenger = Messenger.getGlobalPtr()
'''

from . import Messenger

#: Contains the global :class:`~.Messenger.Messenger` instance.
messenger = Messenger.Messenger()