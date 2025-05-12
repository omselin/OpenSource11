class Map:
    def __init__(self, name: str, locked: bool = False, data: str = ""):
        self.name = name
        self.locked = locked
        self.data = data  # Multiline string representing the map layout