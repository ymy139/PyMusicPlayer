import os
from pathlib import Path
from random import randint
from threading import Thread

from PySide6.QtCore import QUrl, Signal, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioDevice

from .types_ import PlayStatus, MediaInfo, MediaItem, SUPPORTED_AUDIO_FORMATS, PlayMode, PlayerStatus
from .utils import getMediaItemFromPath

class Player(QObject):
        
    playerReady = Signal(list)
    onNextSong = Signal(MediaInfo)
    onPreviousSong = Signal(MediaInfo)
        
    def __init__(self, 
                 outputDevice: QAudioDevice) -> None:
        super().__init__()
        
        self._audioOutput = QAudioOutput(outputDevice)
        self._mediaPlayer = QMediaPlayer()
        self._mediaPlayer.setAudioOutput(self._audioOutput)
        self._mediaPlayer.mediaStatusChanged.connect(self._onMediaStatusChanged)
        
        self._playMode = False
        self._playingStatus = PlayStatus.STOPPED
        self._playerStatus = PlayerStatus.READY
        self._playList: list[MediaItem] = []
        self._currentIndex: int = -1
        
    def play(self, index: int) -> None:
        if index < 0:
            return
        if self._playerStatus == PlayerStatus.READY:
            self._currentIndex = index
            
            self._mediaPlayer.stop()
            try:
                self._mediaPlayer.setSource(
                    QUrl.fromLocalFile(self._playList[index].mediaPath.absolute().as_posix())
                )
            except IndexError:
                return
            self._mediaPlayer.play()
            
            self._playingStatus = PlayStatus.PLAYING
        
    def pause(self) -> None: 
        self._mediaPlayer.pause()
        self._playingStatus = PlayStatus.PAUSED
        
    def unpause(self) -> None: 
        self._mediaPlayer.play()
        self._playingStatus = PlayStatus.PLAYING
        
    def setPositionMs(self, posMs: int) -> None:
        self._mediaPlayer.setPosition(posMs)
    
    def getPositionMs(self) -> int:
        return self._mediaPlayer.position()
    
    def getLengthMs(self) -> int: 
        return self._mediaPlayer.duration()
    
    def getCurrentSongInfo(self) -> MediaInfo:
        return self._playList[self._currentIndex].mediaInfo
    
    def next(self) -> None: 
        if self._playingStatus != PlayStatus.STOPPED:
            if self._playMode == PlayMode.RANDOM:
                self._currentIndex = randint(0, len(self._playList)-1)
            else:
                if self._currentIndex + 1 >= len(self._playList):
                    self._currentIndex = 0
                else:
                    self._currentIndex += 1
                
            self.play(self._currentIndex)
            self.onNextSong.emit(self._playList[self._currentIndex].mediaInfo)
        
    def previous(self) -> None:
        if self._playingStatus != PlayStatus.STOPPED:
            if self._playMode == PlayMode.RANDOM:
                self._currentIndex = randint(0, len(self._playList)-1)
            else:
                if self._currentIndex == 0:
                    self._currentIndex = len(self._playList) - 1
                else:
                    self._currentIndex -= 1
            
            self.play(self._currentIndex)
            self.onPreviousSong.emit(self._playList[self._currentIndex].mediaInfo)
    
    def getCurrentPlayStatus(self) -> PlayStatus: 
        return self._playingStatus
    
    def _onMediaStatusChanged(self, status: QMediaPlayer.MediaStatus) -> None: 
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._playMode == PlayMode.LOOP:
                self.play(self._currentIndex)
            else:
                self.next()
            
    def getCurrentSongIndex(self):
        return self._currentIndex
    
    def changePlayMode(self, mode: PlayMode):
        self._playMode = mode
        
    def getPlayerStatus(self) -> PlayerStatus:
        return self._playerStatus
        
    def updatePlayList(self, musicDir: Path, lyricsDir: Path, cacheDir: Path):
        def update():
            coversDir = cacheDir / "covers"
            coversDir.mkdir(parents=True, exist_ok=True)
            
            self._playerStatus = PlayerStatus.PREPARING
            
            for targetFile in os.listdir(musicDir):
                targetFilePath: Path = (musicDir / targetFile).absolute()
                if targetFile.lower().endswith(SUPPORTED_AUDIO_FORMATS) and targetFilePath.is_file():
                    try: 
                        self._playList.append(getMediaItemFromPath(targetFilePath, lyricsDir, coversDir))
                    except TypeError: 
                        pass
            
            self._playerStatus = PlayerStatus.READY
        
        self._playListUpdateThread = Thread(target=lambda: (update(), self.playerReady.emit(self._playList)), name="playListUpdateThread")
        self._playListUpdateThread.start()
        
    def changeOutputDevice(self, outputDevice: QAudioDevice):
        self._audioOutput.setDevice(outputDevice)
