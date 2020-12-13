class KeyBindDef:

    def __init__(self, name, id, defaultShortcut):
        self.name = name
        self.id = id
        self.shortcut = defaultShortcut

    def asPandaShortcut(self):
        return self.shortcut.replace('+', '-') \
            .replace('ctrl', 'control').lower()

    def asQtShortcut(self):
        return self.shortcut.replace('-', '+') \
            .replace('control', 'ctrl').lower()
