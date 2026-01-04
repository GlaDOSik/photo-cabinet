class PhotoSizeResult:
    def __init__(self, width: int, height: int, width_origin: str, height_origin: str):
        self.width: int = width
        self.height: int = height
        self.width_origin: str = width_origin
        self.height_origin: str = height_origin