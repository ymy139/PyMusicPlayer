# init application and load font before everything
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont

app = QApplication(sys.argv)
QFontDatabase.addApplicationFont("res/fonts/HarmonyOS_Sans_SC_Regular.ttf")
app.setFont(QFont("HarmonyOS Sans SC"))

# main
from pathlib import Path

from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import QTimer
from qtawesome import icon as qtawesomeIcon

from modules.ui.windows import MainWindow
from modules.player import Player
from modules.types_ import PlayStatus, PlayerStatus
from modules.utils import humanizeDuration

player = Player(QMediaDevices.defaultAudioOutput())
window = MainWindow()
sliderPressed = False

def togglePause():
    if player.getPlayerStatus() != PlayerStatus.READY: return
    if player.getCurrentPlayStatus() == PlayStatus.STOPPED: return
    
    if player.getCurrentPlayStatus() == PlayStatus.PAUSED:
        player.unpause()
        window.playStateBar.playPauseButton.setIcon(qtawesomeIcon("fa6.circle-pause", color="#c3ccdf"))
        window.playStateBar.playPauseButton.update()
    else:
        player.pause()
        window.playStateBar.playPauseButton.setIcon(qtawesomeIcon("fa6.circle-play", color="#c3ccdf"))
        window.playStateBar.playPauseButton.update()
        
def onSliderPressed():
    global sliderPressed
    sliderPressed = True
    
def onSliderReleased():
    global sliderPressed
    sliderPressed = False
    player.setPositionMs(int(player.getLengthMs() * (window.playStateBar.musicPlayProgress.value() / 1000)))
    
def play(item: QTableWidgetItem):
    player.play(item.row())
    window.updateMediaInfo(player.getCurrentSongInfo())
    
def updateSliderProgress():
    if player.getPlayerStatus() == PlayerStatus.READY and player.getCurrentPlayStatus() == PlayStatus.PLAYING:
        try: 
            if not sliderPressed:
                window.playStateBar.musicPlayProgress.setValue(int(player.getPositionMs() / player.getLengthMs() * 1000))
        except ZeroDivisionError: pass
        window.playStateBar.musicTimePlayed.setText(humanizeDuration(player.getPositionMs()))

# connect signals
player.playerReady.connect(window.onPlayerReady)
player.onNextSong.connect(window.updateMediaInfo)
player.onPreviousSong.connect(window.updateMediaInfo)
window.playStateBar.playPauseButton.clicked.connect(togglePause)
window.playStateBar.nextButton.clicked.connect(player.next)
window.playStateBar.previousButton.clicked.connect(player.previous)
window.playStateBar.musicPlayProgress.sliderPressed.connect(onSliderPressed)
window.playStateBar.musicPlayProgress.sliderReleased.connect(onSliderReleased)
window.playListPage.playList.itemDoubleClicked.connect(play)

# update slider's progress from time to time
updateTimer = QTimer()
updateTimer.setInterval(500)
updateTimer.timeout.connect(updateSliderProgress)
updateTimer.start()

# test player
player.updatePlayList(Path("D:\\CloudMusic"), Path("G:\\lrc"), Path("cache"))
window.show()
app.exec()