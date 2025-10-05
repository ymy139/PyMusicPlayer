from enum import IntEnum
from dataclasses import dataclass
from pathlib import Path

class PlayStatus(IntEnum):
    STOPPED = 2
    PLAYING = 4
    PAUSED = 8
    
class PlayMode(IntEnum):
    NORMAL = 16
    LOOP = 32
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
