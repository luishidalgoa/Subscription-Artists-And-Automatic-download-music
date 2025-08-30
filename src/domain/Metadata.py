from typing import Optional

class Metadata:
    """
    Modelo de metadatos de audio/música.
    Todos los campos son opcionales y pueden permanecer vacíos (None).
    """

    def __init__(
        self,
        Title: Optional[str] = None,
        Artist: Optional[str] = None,
        Album: Optional[str] = None,
        Date: Optional[str] = None
    ):
        self.Title = Title
        self.Artist = Artist
        self.Album = Album
        self.Date = Date

    def __repr__(self):
        fields = [
            f"Title={self.Title!r}",
            f"Artist={self.Artist!r}",
            f"Album={self.Album!r}",
            f"Date={self.Date!r}",
        ]
        return f"<Metadata {' | '.join(fields)}>"
