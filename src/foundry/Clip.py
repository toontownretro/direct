from .CreateEditDelete import CreateEditDelete, CreateReference, DeleteReference

class Clip(CreateEditDelete):

    Name = "Clip Solid(s)"

    def __init__(self, solids, plane, keepFront, keepBack):
        CreateEditDelete.__init__(self)
        self.solids = solids
        self.plane = plane
        self.keepFront = keepFront
        self.keepBack = keepBack
        self.firstRun = True

    def cleanup(self):
        self.solids = None
        self.plane = None
        self.keepBack = None
        self.keepFront = None
        self.firstRun = None

    def do(self):
        if self.firstRun:
            self.firstRun = False

            for solid in self.solids:
                ret, back, front = solid.split(self.plane, base.document.idGenerator)
                if not ret:
                    continue
                front.selected = back.selected = solid.selected
                if self.keepBack:
                    self.create(CreateReference(solid.parent.id, back))
                else:
                    back.delete()

                if self.keepFront:
                    self.create(CreateReference(solid.parent.id, front))
                else:
                    front.delete()

                self.delete(DeleteReference(solid))

        CreateEditDelete.do(self)
