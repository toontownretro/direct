"""DistributedActor module: contains the DistributedActor class"""

import DistributedNode
import Actor

class DistributedActor(DistributedNode.DistributedNode, Actor.Actor):
    """Distributed Actor class:"""

    def __init__(self, cr):
        try:
            self.DistributedActor_initialized
        except:
            self.DistributedActor_initialized = 1
            DistributedNode.DistributedNode.__init__(self, cr)

            # Since actors are probably fairly heavyweight, we'd
            # rather cache them than delete them if possible.
            self.setCacheable(1)
            
        return None

    def disable(self):
        # remove all anims, on all parts and all lods
        Actor.Actor.unloadAnims(None, None, None)
        DistributedNode.DistributedNode.disable(self)
