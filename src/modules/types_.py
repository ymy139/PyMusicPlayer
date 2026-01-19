from enum import IntEnum, Enum
from dataclasses import dataclass
from pathlib import Path

class PlayStatus(IntEnum):
    STOPPED = 2
    PLAYING = 4
    PAUSED = 8
    
class PlayMode(IntEnum):
    LOOP_LIST = 16
    LOOP_ONE = 32
    RANDOM = 64
    
class PlayerStatus(IntEnum):
    READY = 128
    PREPARING = 256
    
@dataclass
class MediaInfo:
    title: str
    artist: str 
    album: str
    lengthMs: int
    coverPath: Path | None
    lyricsPath: Path | None

@dataclass
class MediaItem:
    mediaPath: Path
    mediaInfo: MediaInfo
    
SUPPORTED_AUDIO_FORMATS = (".mp3", ".flac")

@dataclass
class LrcObject:
    """Used to store a line of lyric"""
    timeMs: int
    text: str

class BaseDirection:
    """define the base direction of the cursor, 
    every direction should be a subclass of BaseDirection.  
    This object's x and y's orgin point is center of the window, 
    just like this:
    
    | (-1,1) | (0,1) | (1,1) |
    |--------|-------|-------|
    | (-1,0) | (0,0) | (1,0) |
    | (-1,-1)| (0,-1)| (1,-1)|
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.x = x
        self.y = y

class CursorDirection(Enum):
    LEFT = BaseDirection(-1, 0)
    RIGHT = BaseDirection(1, 0)
    TOP = BaseDirection(0, 1)
    BOTTOM = BaseDirection(0, -1)
    TOP_LEFT = BaseDirection(-1, 1)
    TOP_RIGHT = BaseDirection(1, 1)
    BOTTOM_LEFT = BaseDirection(-1, -1)
    BOTTOM_RIGHT = BaseDirection(1, -1)
