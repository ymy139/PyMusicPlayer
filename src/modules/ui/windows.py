from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, 
                               QStackedLayout, QFrame, QListWidgetItem, QTableWidgetItem)
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QMouseEvent, QIcon
from qtawesome import icon as qtawesomeIcon

from .widgets import SideMenuBar, TitleBar, PlayStateBar, Pages
from ..utils import getCursorDirection, humanizeDuration
from ..types_ import MediaItem, MediaInfo

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._mousePressed = False
        self._contentsMargin = 7
        
        self._centralWidget = QWidget()
        self._centralWidget.setMouseTracking(True)
        self._centralWidget.setObjectName("centralWidget")
        self._centralWidget.setStyleSheet("""
                QWidget#centralWidget { 
                    border: 2px solid #343b48; 
                    border-radius: 5px; 
                }
                
                QWidget {
                    outline: none;
                }
            """)
        self._centralLayout = QVBoxLayout()
        self._centralLayout.setContentsMargins(self._contentsMargin, 
                                               self._contentsMargin, 
                                               self._contentsMargin, 
                                               self._contentsMargin)
        self._centralWidget.setLayout(self._centralLayout)
        
        self.setCentralWidget(self._centralWidget)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #2c313c; border-radius: 5px;")
        
        self.setupWidgets()
        self.setupSignals()
        
    def setupWidgets(self):
        self._contextLayout = QHBoxLayout()
        self._contextLayout.setContentsMargins(0, 0, 0, 0)
        
        self._contextWidget = QWidget()
        self._contextWidget.setMouseTracking(True)
        self._contextWidget.setLayout(self._contextLayout)
        
        self.sideMenuBar = SideMenuBar()
        self.sideMenuBar.setStyleSheet("background-color: #1b1e23; border-radius: 5px;")
        self.sideMenuBar.setMouseTracking(True)
        
        rightLayout = QVBoxLayout()
        
        self.titleBar = TitleBar()
        self.titleBar.setStyleSheet("background-color: #343b48; border-radius: 5px;")
        self.titleBar.setMouseTracking(True)
        
        self._pagesLayout = QStackedLayout()
        self._pagesLayout.setContentsMargins(0, 0, 0, 0)
        
        self.pagesFrame = QFrame()
        self.pagesFrame.setLayout(self._pagesLayout)
        self.pagesFrame.setStyleSheet("background-color: #2c313c; border-radius: 5px;")
        self.pagesFrame.setMouseTracking(True)
        
        self.homePage = Pages.HomePage()
        self.playListPage = Pages.PlayListPage()
        self.musicDetailPage = Pages.MusicDetailPage()
        self.aboutPage = Pages.AboutPage()
        self.settingsPage = Pages.SettingsPage()
        
        self._pagesLayout.addWidget(self.homePage)
        self._pagesLayout.addWidget(self.playListPage)
        self._pagesLayout.addWidget(self.musicDetailPage)
        self._pagesLayout.addWidget(self.aboutPage)
        self._pagesLayout.addWidget(self.settingsPage)
        
        self.playStateBar = PlayStateBar()
        self.playStateBar.setStyleSheet("background-color: #343b48; border-radius: 5px;")
        self.playStateBar.setMouseTracking(True)
        
        rightLayout.addWidget(self.titleBar)
        rightLayout.addWidget(self.pagesFrame)
        rightLayout.addWidget(self.playStateBar)
        
        self._contextLayout.addWidget(self.sideMenuBar)
        self._contextLayout.addLayout(rightLayout)
        self._centralLayout.addWidget(self._contextWidget)
        
    def setupSignals(self):
        self.titleBar.minimizeButton.clicked.connect(self.showMinimized)
        self.titleBar.maximizeButton.clicked.connect(self.toggleMaximize)
        self.titleBar.closeButton.clicked.connect(self.close)
        self.sideMenuBar.menuList.itemClicked.connect(self.onMenuClicked)
        
    def toggleMaximize(self):
        if self.isMaximized():
            self.showNormal()
            self.setStyleSheet("background-color: #2c313c; border-radius: 5px;")
            self.titleBar.maximizeButton.setIcon(qtawesomeIcon("fa6.square", 
                                                               color="#c3ccdf"))
            self.resize(self._lastNormalSize)
        else:
            self.showMaximized()
            self.setStyleSheet("background-color: #2c313c;")
            self.titleBar.maximizeButton.setIcon(qtawesomeIcon("fa6.window-restore", 
                                                               color="#c3ccdf"))
            self._lastNormalSize = self.size()
        self.update()
    
    def mousePressEvent(self, a0: QMouseEvent):
        if a0 != None :
            self._mousePressed = True
            self._dragDirection = getCursorDirection(self.size(), 
                                                     a0.position().toPoint(), 
                                                     self._contentsMargin)
            if  a0.button() == Qt.MouseButton.LeftButton:
                self._dragRelativePosition = a0.position().toPoint()
                self._dragGlobalPosition = a0.globalPosition().toPoint()
            a0.accept()
    
    def mouseMoveEvent(self, a0: QMouseEvent):
        if a0 != None:
            if self._mousePressed != True:
                if not self.isMaximized():
                    # updata the cursor if the mouse is over the margins
                    cursorPos = a0.position().toPoint()
                    direction = getCursorDirection(self.size(), 
                                                   cursorPos, 
                                                   self._contentsMargin)
                    
                    if direction == "top" or direction == "bottom":
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    elif direction == "left" or direction == "right":
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif direction == "top-left" or direction == "bottom-right":
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif direction == "top-right" or direction == "bottom-left":
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                # resize the window if the mouse is draging the margins
                if  self._dragDirection != None and \
                    self._dragGlobalPosition != None and \
                    not self.isMaximized():
                        currentPos = a0.globalPosition().toPoint()
                        delta = currentPos - self._dragGlobalPosition
                        
                        windowGeometry = self.geometry()
                        x = windowGeometry.x()
                        y = windowGeometry.y()
                        width = windowGeometry.width()
                        height = windowGeometry.height()  
                        
                        if "top" in self._dragDirection:
                            height -= delta.y()
                            if height >= self.minimumHeight(): y += delta.y()
                        if "bottom" in self._dragDirection:
                            height += delta.y()
                        if "left" in self._dragDirection:
                            width -= delta.x()
                            if width >= self.minimumWidth(): x += delta.x()
                        if "right" in self._dragDirection:
                            width += delta.x()
                        
                        width = max(width, self.minimumWidth())
                        height = max(height, self.minimumHeight())
                        
                        self.setGeometry(QRect(x, y, width, height))
                        
                        self._dragGlobalPosition = currentPos
            
                # check if mouse is over the title bar and not over the buttons
                # and if so, move the window
                if  a0.buttons() == Qt.MouseButton.LeftButton and \
                    self._dragRelativePosition != None and \
                    self.titleBar.minimizeButton.underMouse() == False and \
                    self.titleBar.maximizeButton.underMouse() == False and \
                    self.titleBar.closeButton.underMouse() == False and \
                    self.titleBar.underMouse() == True:
                        
                        globalPosition = a0.globalPosition().toPoint()
                        
                        if self.isMaximized():
                            self.toggleMaximize()
                            
                            if self._dragRelativePosition.x() > self._lastNormalSize.width():
                                movePoint = \
                                    globalPosition - \
                                    QPoint(int(self._lastNormalSize.width() / 2), 
                                           a0.position().toPoint().y())
                                self.move(movePoint)
                                
                                self._dragRelativePosition = \
                                    globalPosition - self.frameGeometry().topLeft()
                        else:
                            self.move(globalPosition - self._dragRelativePosition)
                            
            a0.accept()
            
    def mouseDoubleClickEvent(self, a0: QMouseEvent):
        if a0 != None:
            # we don't need to check if mouse not over the buttons
            # because once the mouse click the button, it will
            # trigger minimization, maximization, or closure
            # so it can't trigger this event, we can move the
            # window directly
            if  a0.button() == Qt.MouseButton.LeftButton and \
                self.titleBar.underMouse() == True:
                    
                    self.toggleMaximize()

            a0.accept()
                
    def mouseReleaseEvent(self, a0) -> None:
        self._mousePressed = False
        self._dragDirection = None
        self._dragGlobalPosition = None
        self._dragRelativePosition = None
        
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        return super().mouseReleaseEvent(a0)
        
    def onMenuClicked(self, item: QListWidgetItem):
        if item.data(Qt.ItemDataRole.UserRole) == "Home":
            self._pagesLayout.setCurrentIndex(0)
            self.playStateBar.showDetails()
        elif item.data(Qt.ItemDataRole.UserRole) == "PlayList":
            self._pagesLayout.setCurrentIndex(1)
            self.playStateBar.showDetails()
        elif item.data(Qt.ItemDataRole.UserRole) == "PlayDetail":
            self._pagesLayout.setCurrentIndex(2)
            self.playStateBar.hideDetails()
        elif item.data(Qt.ItemDataRole.UserRole) == "About":
            self._pagesLayout.setCurrentIndex(3)
            self.playStateBar.showDetails()
        elif item.data(Qt.ItemDataRole.UserRole) == "Settings":
            self._pagesLayout.setCurrentIndex(4)
            self.playStateBar.showDetails()
            
    def onPlayerReady(self, playList: list[MediaItem]):
        self.playListPage.songCount.setText(f"当前列表中有 {len(playList)} 首歌曲")
        self.playListPage.progressBar.stop()
        self.playListPage.syncStatus.setText("播放列表已更新完成")
        self.playListPage.syncButton.setIcon(self.playListPage.SyncButtonIcon.finish)
        
        self.playListPage.playList.setRowCount(len(playList))
        
        for index, item in enumerate(playList):
            if item.mediaInfo.coverPath and item.mediaInfo.coverPath.exists():
                cover = QIcon()
                cover.addFile(str(item.mediaInfo.coverPath), mode=QIcon.Mode.Normal, state=QIcon.State.Off)
                cover.addFile(str(item.mediaInfo.coverPath), mode=QIcon.Mode.Selected, state=QIcon.State.Off)
                tableItem = QTableWidgetItem(item.mediaInfo.title)
                tableItem.setToolTip(item.mediaInfo.title)
                tableItem.setIcon(QIcon(cover))
                self.playListPage.playList.setItem(index, 0, tableItem)
            else:
                cover = QIcon()
                cover.addFile("res/imgs/ddefaultCover.png", mode=QIcon.Mode.Normal, state=QIcon.State.Off)
                cover.addFile("res/imgs/ddefaultCover.png", mode=QIcon.Mode.Selected, state=QIcon.State.Off)
                tableItem = QTableWidgetItem(item.mediaInfo.title)
                tableItem.setToolTip(item.mediaInfo.title)
                tableItem.setIcon(QIcon(cover))
                self.playListPage.playList.setItem(index, 0, tableItem)
            
            tableItem = QTableWidgetItem(item.mediaInfo.artist)
            tableItem.setToolTip(item.mediaInfo.artist)
            self.playListPage.playList.setItem(index, 1, tableItem)
            
            tableItem = QTableWidgetItem(item.mediaInfo.album)
            tableItem.setToolTip(item.mediaInfo.album)
            self.playListPage.playList.setItem(index, 2, tableItem)

            self.playListPage.playList.setItem(index, 3, QTableWidgetItem(humanizeDuration(item.mediaInfo.lengthMs)))
            
    def updateMediaInfo(self, mediaInfo: MediaInfo):
        self.playStateBar.setMediaInfo(mediaInfo)
        self.musicDetailPage.setMediaInfo(mediaInfo)
