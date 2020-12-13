from .CreateEditDelete import CreateEditDelete, CreateReference

class Create(CreateEditDelete):

    Name = "Create Object"

    def __init__(self, parentId, mapObject):
        CreateEditDelete.__init__(self)
        self.create(CreateReference(parentId, mapObject))

class MultiCreate(CreateEditDelete):

    Name = "Create Object(s)"

    def __init__(self, creations):
        CreateEditDelete.__init__(self)
        for creation in creations:
            self.create(CreateReference(creation[0], creation[1]))
