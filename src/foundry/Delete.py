from .CreateEditDelete import CreateEditDelete, DeleteReference

class Delete(CreateEditDelete):

    Name = "Delete Object(s)"

    def __init__(self, mapObject):
        CreateEditDelete.__init__(self)
        if isinstance(mapObject, list):
            for obj in mapObject:
                self.delete(DeleteReference(obj))
        else:
            self.delete(DeleteReference(mapObject))
