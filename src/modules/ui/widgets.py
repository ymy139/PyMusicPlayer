from typing import Literal, Callable
from dataclasses import dataclass

from PySide6.QtWidgets import (QFrame, QWidget, QVBoxLayout, QLabel, QListWidget, 
                               QListWidgetItem, QSpacerItem, QSizePolicy, QHBoxLayout,
                               QPushButton, QSlider, QScrollArea, QLayout, QProgressBar,
                               QTableWidget, QHeaderView, QAbstractItemView, QStyledItemDelegate,
                               QStyleOptionViewItem, QStyle, QTextBrowser)
from PySide6.QtCore import (Qt, QSize, QPropertyAnimation, QTimer, Property, QEasingCurve, 
                            QParallelAnimationGroup, QSequentialAnimationGroup, QEvent, 
                            QModelIndex, QPersistentModelIndex, QAbstractItemModel)
from PySide6.QtGui import (QPixmap, QFont, QResizeEvent, QShowEvent, QColor, QPaintEvent, 
                           QPainter, QBrush)
from qtawesome import icon as qtawesomeIcon

from ..utils import createRoundedPixmap, parseLrc, humanizeDuration
from ..types_ import MediaInfo

class IndeterminateProgressBar(QProgressBar):
    def __init__(self, parent: QWidget | None = None, slowCoefficient: float = 1.0):
        super().__init__(parent=parent)
        self.setMaximumHeight(4)
        self.setMinimumHeight(4)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self._shortPos = 0
        self._longPos = 0
        self._barColor = QColor(Qt.GlobalColor.white)
        self._shortBarAni = QPropertyAnimation(self, b'shortPos', self)
        self._longBarAni = QPropertyAnimation(self, b'longPos', self)

        self._aniGroup = QParallelAnimationGroup(self)
        self._longBarAniGroup = QSequentialAnimationGroup(self)

        self._shortBarAni.setDuration(round(833*slowCoefficient))
        self._shortBarAni.setStartValue(0)
        self._shortBarAni.setEndValue(1.45)
        
        self._longBarAni.setDuration(round(1167*slowCoefficient))
        self._longBarAni.setStartValue(0)
        self._longBarAni.setEndValue(1.75)
        self._longBarAni.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._aniGroup.addAnimation(self._shortBarAni)
        self._longBarAniGroup.addPause(785)
        self._longBarAniGroup.addAnimation(self._longBarAni)
        self._aniGroup.addAnimation(self._longBarAniGroup)
        self._aniGroup.setLoopCount(-1)
        
        self.start()

    @Property(float)
    def shortPos(self): # pyright: ignore[reportRedeclaration]
        return self._shortPos

    @shortPos.setter
    def shortPos(self, p):
        self._shortPos = p
        self.update()
        
    @Property(float)
    def longPos(self): # pyright: ignore[reportRedeclaration]
        return self._longPos

    @longPos.setter
    def longPos(self, p):
        self._longPos = p
        self.update()

    def start(self):
        self.shortPos = 0 # pyright: ignore[reportAttributeAccessIssue]
        self.longPos = 0 # pyright: ignore[reportAttributeAccessIssue]
        self._aniGroup.start()
        self.update()

    def stop(self):
        self._aniGroup.stop()
        self.shortPos = 0 # pyright: ignore[reportAttributeAccessIssue]
        self.longPos = 0 # pyright: ignore[reportAttributeAccessIssue]
        self.update()

    def setBarColor(self, color: QColor):
        self._barColor = color

    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._barColor)

        # draw short bar
        x = int((self.shortPos - 0.4) * self.width()) # pyright: ignore[reportOperatorIssue]
        w = int(0.2 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)

        # draw long bar
        x = int((self.longPos - 0.6) * self.width()) # pyright: ignore[reportOperatorIssue]
        w = int(0.4 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)

class LyricWidget(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.verticalScrollBar().setVisible(False)
        self.setHtml("""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset='utf-8'>
                    <style>
                        body {
                            background-color: rgb(44, 49, 60);
                            color: #c3ccdf;
                        }
                    </style>
                </head>
                <body>
                </body>
            </html>
        """)
        
        self.parsedLrcContent = []
        self.getTime: Callable[[], int] = lambda: 0
        self.displayTextHeader = """
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: HarmonyOS Sans SC;
                    background-color: rgb(44, 49, 60);
                    color: #c3ccdf;
                }
            </style>
            </head>
            <body>
                <p style='text-align: center;'>
        """
        
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(100)
        self.updateTimer.timeout.connect(self.updateDisplay)
        
    def setLrcContent(self, lrcContent: str):
        self.updateTimer.stop()
        self.parsedLrcContent = parseLrc(lrcContent)
        self.parsedLrcContent.sort(key = lambda x: x.timeMs)
        self.updateTimer.start()
        
    def setGetTimeFunc(self, func: Callable[[], int]):
        self.getTime = func
        
    def updateDisplay(self):
        nowTimeMs = self.getTime()
        
        displayText = self.displayTextHeader
        parsedLrcContent = self.parsedLrcContent
        
        if len(parsedLrcContent) == 1:
            displayText += ('<b style="font-size: 22px">' + parsedLrcContent[0].text + '</b>')
        else:
            for i, lrc in enumerate(parsedLrcContent):
                if lrc.timeMs >= nowTimeMs:
                    parsedLrcContent = parsedLrcContent[i-1:]
                    break
                
            displayText += ('<br/><b style="font-size: 22px">' + parsedLrcContent[0].text + '</b>')
                
            for lrc in parsedLrcContent[1:]:
                displayText += ('<br/><br/><span style="font-size: 16px">' + lrc.text + '</span>')
            
        displayText += "</p></body></html>"
        
        self.setHtml(displayText)
        self.update()

class MarqueeLabel(QScrollArea):
    def __init__(self):
        super().__init__()
        self.animation = QPropertyAnimation(self.horizontalScrollBar(), b"value")
        self.initUI()
        
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("MarqueeLabel")
        self.setWidget(self.container)
        
        self.autoAdjustSize()
        self.checkIsScrollNeeded()

    def initUI(self):
        self.container = QFrame()
        
        containerLayout = QHBoxLayout(self.container)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        
        self.label = QLabel("Hello, World!"*10)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        containerLayout.addWidget(self.label)
        
    def autoAdjustSize(self):
        viewportHeight = self.viewport().height() # pyright: ignore[reportOptionalMemberAccess]
        
        self.container.setMinimumHeight(viewportHeight)
        
        self.label.setMinimumHeight(viewportHeight)
        self.label.setMaximumHeight(viewportHeight)
        
        self.container.adjustSize()
        self.label.adjustSize()
        
    def checkIsScrollNeeded(self):
        labelWidth = self.label.sizeHint().width()
        viewportWidth = self.viewport().width() # pyright: ignore[reportOptionalMemberAccess]
        
        self.stopAllAnimations()
        
        if labelWidth > viewportWidth:
            self.horizontalScrollBar().setValue(0) # pyright: ignore[reportOptionalMemberAccess]
            self.startScroll((labelWidth - viewportWidth) * 15)
        else:
            self.horizontalScrollBar().setValue(0) # pyright: ignore[reportOptionalMemberAccess]
            
    def stopAllAnimations(self):
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
        try:
            self.timer.stop()
        except:
            pass
                
    def startScroll(self, duration: int):
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        
        def scrollToRight():
            self.animation.setDuration(duration)
            self.animation.setStartValue(0)
            self.animation.setEndValue(
                self.horizontalScrollBar().maximum() # pyright: ignore[reportOptionalMemberAccess]
            )
            
            self.timer.timeout.disconnect()
            self.timer.timeout.connect(scrollToLeft)
            self.animation.finished.connect(lambda: self.timer.start(1500))
            
            self.animation.start()
            
        def scrollToLeft():
            self.animation.setDuration(duration)
            self.animation.setStartValue(
                self.horizontalScrollBar().maximum() # pyright: ignore[reportOptionalMemberAccess]
            )
            self.animation.setEndValue(0)
            
            self.timer.timeout.disconnect()
            self.timer.timeout.connect(scrollToRight)
            self.animation.finished.connect(lambda: self.timer.start(1500))
            
            self.animation.start()
        
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(scrollToRight)
        self.timer.start(1500)
        
    def resizeEvent(self, a0: QResizeEvent) -> None:
        super().resizeEvent(a0)
        self.autoAdjustSize()
        self.checkIsScrollNeeded()
        
    def showEvent(self, a0: QShowEvent) -> None:
        super().showEvent(a0)
        self.autoAdjustSize()
        self.checkIsScrollNeeded()
        
    def setText(self, text: str):
        self.label.setText(text)
        self.autoAdjustSize()
        self.checkIsScrollNeeded()
        
    def setFont(self, a0) -> None:
        self.label.setFont(a0)
        super().setFont(a0)
        self.autoAdjustSize()
        self.checkIsScrollNeeded()

class TitleCard(QFrame):
    """Title Card, size 250 x 70"""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setGeometry(0, 0, 250, 70)
        self.setMaximumSize(250, 70)
        self.setMinimumSize(250, 70)
        self.setObjectName("titleCard")
        self.setupWidgets()
        
    def setupWidgets(self):
        icon = QLabel(self)
        icon.setGeometry(0, 0, 70, 70)
        icon.setScaledContents(True)
        icon.setPixmap(QPixmap("./res/imgs/icons/icon.ico"))
        
        title = QLabel("PyMusicPlayer", self)
        title.setGeometry(70, 10, 180, 30)
        _font = self.font()
        _font.setPointSize(17)
        title.setFont(_font)
        title.setStyleSheet("color: #c3ccdf;")
        
        subtitle = QLabel("Simple, beautiful music player", self)
        subtitle.setGeometry(70, 40, 180, 20)
        _font = self.font()
        _font.setPointSize(10)
        subtitle.setFont(_font)
        subtitle.setStyleSheet("color: #5688e0;")
    
class Line(QFrame):
    def __init__(self, 
                 parent: QWidget | None = None, 
                 color: str | None = None, 
                 shape: Literal["H", "V"] = "H") -> None:
        """A line widget.  
        **PLEASE DO NOT SET STYLESHEET FOR THIS WIDGET.**

        Args:
            parent (QWidget | None, optional): Parent of this widget. Defaults to None.
            color (str, optional): Color of the line, **ONLY** can be HEX(`#123abc`). Defaults to None.
            shape (str, optional): Shape of the line, can be "H" or "V". Defaults to "H".
        """
        super().__init__(parent)
        if color != None: self.setColor(color)
        if shape == "H":
            self.setMaximumHeight(3)
            self.setMinimumHeight(3)
        elif shape == "V":
            self.setMaximumWidth(3)
            self.setMinimumWidth(3)
            self.setStyleSheet("background-color: none; border-radius: 2px;")
        self.setObjectName("Line")
    def setColor(self, color: str) -> None:
        self.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
    
class SideMenuBar(QFrame):
    """Side menu bar widget. Minimum size: 260 x 500, maximun size: 260 x Infinite"""
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self._layout)
        self.setObjectName("SideMenuBar")
        self.setMinimumHeight(500)
        self.setMaximumWidth(260)
        self.setMinimumWidth(260)
        self.setupWidgets()
        
    def setupWidgets(self):
        titleCard = TitleCard()
        titleCard.setStyleSheet("background-color: #21252d; border-radius: 5px;")
        
        self.menuList = QListWidget()
        self.menuList.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #c3ccdf;
                font-size: 14px;
	            padding: 5px 0;
            }
            QListWidget::item {
                padding: 5px 5px;
                border-radius: 10px;
                margin: 5px 5px;
                border-left: 3px solid rgba(0, 0, 0, 0);
            }
            QListWidget::item:selected {
                background-color: #2c313c;
                border-left: 3px solid #568af2;
                color: #f5f6f9;
            }
            QListWidget::item:hover {
                background-color: #21252d;
            }""")
        self.menuList.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.menuList.setIconSize(QSize(25, 25))
        _font = self.font()
        _font.setPointSize(11)
        _font.setBold(False)
        self.menuList.setFont(_font)
        
        # init menu items
        # `id` is used to identify the menu item when the menu item is clicked.
        menuItems = [
            {"awsIconId": "fa5s.home", "text": " 主页", "id": "Home"},
            {"awsIconId": "fa5s.list-ul", "text": " 播放列表", "id": "PlayList"},
            {"awsIconId": "fa5s.music", "text": " 音乐详情页", "id": "PlayDetail"},
            {"awsIconId": "fa6s.circle-info", "text": " 关于", "id": "About"},
            {"awsIconId": "fa6s.gear", "text": " 设置", "id": "Settings"}]
        _font = self.font()
        _font.setPointSize(12)
        for i in menuItems:
            item = QListWidgetItem(qtawesomeIcon(i["awsIconId"], color="#c3ccdf", color_active="#f5f6f9"), i["text"])
            item.setData(Qt.ItemDataRole.UserRole, i["id"])
            item.setFont(_font)
            self.menuList.addItem(item)
        self.menuList.item(0).setSelected(True)  # pyright: ignore[reportOptionalMemberAccess]
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        copyleft = QLabel()
        copyleft.setText("Copyleft 2025 by ymy139\n版权部分所有，遵循GNU GPLv3发布\n更多信息详见“关于”")
        copyleft.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyleft.setStyleSheet("color: #5d626d")
        _font = self.font()
        _font.setPointSize(10)
        copyleft.setFont(_font)
        
        self._layout.addWidget(titleCard)
        self._layout.addWidget(Line(color="#21252d", shape="H"))
        self._layout.addWidget(self.menuList)
        self._layout.addItem(spacer)
        self._layout.addWidget(Line(color="#21252d", shape="H"))
        self._layout.addWidget(copyleft)

class TitleBar(QFrame):
    """title bar widget. Minimum size: 500 x 40, maximun size: Infinite x 40"""
    def __init__(self) -> None:
        super().__init__()
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 5, 5, 5)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)
        self.setMinimumSize(500, 40)
        self.setObjectName("TitleBar")
        self.setMaximumHeight(40)
        self.setupWidgets()
        
    def setupWidgets(self):
        styleSheet = """
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6b7994;
            }
            
            QPushButton:pressed {
                background-color: #616e87;
            }
            """
            
        # TODO: config item
        self.label = QLabel("见过沧海桑田，望过白日飞升，走过拙山枯水，笑过月隐晦明。")
        self.label.setStyleSheet("color: #848fa3")
        self.label.setMinimumWidth(195)
        _font = self.font()
        _font.setPointSize(10)
        self.label.setFont(_font)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        self.minimizeButton = QPushButton()
        self.minimizeButton.setMaximumSize(30, 30)
        self.minimizeButton.setMinimumSize(30, 30)
        self.minimizeButton.setIconSize(QSize(20, 20))
        self.minimizeButton.setStyleSheet(styleSheet)
        self.minimizeButton.setIcon(qtawesomeIcon("fa6s.minus", 
                                                  color="#c3ccdf"))
        
        self.maximizeButton = QPushButton()
        self.maximizeButton.setMaximumSize(30, 30)
        self.maximizeButton.setMinimumSize(30, 30)
        self.maximizeButton.setIconSize(QSize(20, 20))
        self.maximizeButton.setStyleSheet(styleSheet)
        self.maximizeButton.setIcon(qtawesomeIcon("fa6.square", 
                                                  color="#c3ccdf"))
        
        self.closeButton = QPushButton()
        self.closeButton.setMaximumSize(30, 30)
        self.closeButton.setMinimumSize(30, 30)
        self.closeButton.setIconSize(QSize(20, 20))
        self.closeButton.setStyleSheet(styleSheet)  
        self.closeButton.setIcon(qtawesomeIcon("fa6s.xmark", 
                                               color="#c3ccdf"))
        
        self._layout.addWidget(self.label)
        self._layout.addItem(spacer)
        self._layout.addWidget(self.minimizeButton)
        self._layout.addWidget(self.maximizeButton)
        self._layout.addWidget(self.closeButton)
    
class PlayStateBar(QFrame):
    """
    Play state bar widget. 
    
    Maxinum size: Infinite x 105, minimum size: 300 x 105 (show details)
    
    Maxinum size: Infinite x 55, minimum size: 300 x 55 (hide details)
    """
    def __init__(self) -> None:
        super().__init__()
        self._layout = QHBoxLayout(self)
        self._isShowingDetails = True
        self._playerSetPos = None
        self.setLayout(self._layout)
        self.setupWidgets()
        self.setObjectName("PlayStateBar")
        self.setMaximumHeight(105)
        self.setMinimumHeight(105)
        self.setMinimumWidth(300)
        
    def setupWidgets(self):
        self._layout.setContentsMargins(5, 5, 5, 5)
        
        self.musicCover = QLabel()
        self.musicCover.setMaximumSize(95, 95)
        self.musicCover.setMinimumSize(95, 95)
        _font = self.font()
        _font.setPointSize(16)
        self.musicCover.setFont(_font)
        self.musicCover.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.musicCover.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.musicCover.setStyleSheet("""
            border: 1px solid #20242c; 
            border-radius: 5px; color: #848fa3;
        """)
        self.musicCover.setPixmap(createRoundedPixmap(QPixmap("res/imgs/defaultCover.png"), 30))
        self.musicCover.setScaledContents(True)
        
        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(0)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        
        self.musicTitle = MarqueeLabel()
        self.musicTitle.setText("暂无歌曲")
        _font = self.font()
        _font.setPointSize(12)
        _font.setBold(True)
        self.musicTitle.setFont(_font)
        self.musicTitle.setMaximumHeight(25)
        self.musicTitle.setStyleSheet("border: none; color: #c3ccdf;")
        
        self.musicArtist = MarqueeLabel()
        self.musicArtist.setText("暂无歌手")
        _font = self.font()
        _font.setPointSize(9)
        self.musicArtist.setFont(_font)
        self.musicArtist.setMaximumHeight(20)
        self.musicArtist.setStyleSheet("border: none; color: #c3ccdf;")
        
        self.musicPlayProgress = QSlider(Qt.Orientation.Horizontal)
        self.musicPlayProgress.setRange(0, 1000)
        self.musicPlayProgress.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background-color: rgba(0, 0, 0, 100);
                border-radius: 2px;
            }

            QSlider::sub-page:horizontal {
                background: #5d98cc;
                height: 4px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                border: 1px solid rgb(209, 209, 209);
                width: 16px;
                margin: -7px 0;
                border-radius: 9px;
                background-color: qradialgradient(
                    spread:pad, 
                    cx:0.5, 
                    cy:0.5, 
                    radius:0.5, 
                    fx:0.5, 
                    fy:0.5,
                    stop:0 #5d98cc,
                    stop:0.37 #5d98cc,
                    stop:0.47 rgb(209, 209, 209),
                    stop:1 rgb(209, 209, 209)
                );
            }

            QSlider::handle:horizontal:hover {
                background-color: qradialgradient(
                    spread:pad, 
                    cx:0.5, 
                    cy:0.5, 
                    radius:0.5, 
                    fx:0.5, 
                    fy:0.5,
                    stop:0 #5d98cc,
                    stop:0.45 #5d98cc,
                    stop:0.55 rgb(209, 209, 209),
                    stop:1 rgb(209, 209, 209)
                );
            }

            QSlider::handle:horizontal:pressed {
                background-color: qradialgradient(
                    spread:pad, 
                    cx:0.5, 
                    cy:0.5, 
                    radius:0.5, 
                    fx:0.5, 
                    fy:0.5,
                    stop:0 #5d98cc,
                    stop:0.4 #5d98cc,
                    stop:0.5 rgb(209, 209, 209),
                    stop:1 rgb(209, 209, 209)
                );
            }
            """)
        
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setContentsMargins(5, 0, 5, 0)
        self.bottomLayout.setSpacing(5)
        
        self.musicTimePlayed = QLabel("0:00")
        self.musicTimePlayed.setStyleSheet("color: #c3ccdf;")
        
        
        pushButtonStyleSheet = """
            QPushButton {
                background-color: transparent;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #6b7994;
            }
            
            QPushButton:pressed {
                background-color: #616e87;
            }
        """
        
        self.previousButton = QPushButton()
        self.previousButton.setMaximumSize(25, 25)
        self.previousButton.setMinimumSize(25, 25)
        self.previousButton.setStyleSheet(pushButtonStyleSheet)
        self.previousButton.setIcon(qtawesomeIcon("fa6s.backward-step", color="#c3ccdf"))
        self.previousButton.setIconSize(QSize(18, 18))
        
        self.playPauseButton = QPushButton()
        self.playPauseButton.setMaximumSize(25, 25)
        self.playPauseButton.setMinimumSize(25, 25)
        self.playPauseButton.setStyleSheet(pushButtonStyleSheet)
        self.playPauseButton.setIcon(qtawesomeIcon("fa6.circle-play", color="#c3ccdf"))
        self.playPauseButton.setIconSize(QSize(20, 20))
        
        self.nextButton = QPushButton()
        self.nextButton.setMaximumSize(25, 25)
        self.nextButton.setMinimumSize(25, 25)
        self.nextButton.setStyleSheet(pushButtonStyleSheet)
        self.nextButton.setIcon(qtawesomeIcon("fa6s.forward-step", color="#c3ccdf"))
        self.nextButton.setIconSize(QSize(18, 18))
        
        self.musicTimeTotal = QLabel("0:00")
        self.musicTimeTotal.setStyleSheet("color: #c3ccdf;")
        
        self._layout.addWidget(self.musicCover)
        self.rightLayout.addWidget(self.musicTitle)
        self.rightLayout.addWidget(self.musicArtist)
        self.rightLayout.addWidget(self.musicPlayProgress)
        self.bottomLayout.addWidget(self.musicTimePlayed)
        self.bottomLayout.addItem(QSpacerItem(40, 
                                              20, 
                                              QSizePolicy.Policy.Expanding, 
                                              QSizePolicy.Policy.Minimum))
        self.bottomLayout.addWidget(self.previousButton)
        self.bottomLayout.addWidget(self.playPauseButton)
        self.bottomLayout.addWidget(self.nextButton)
        self.bottomLayout.addItem(QSpacerItem(40, 
                                              20, 
                                              QSizePolicy.Policy.Expanding, 
                                              QSizePolicy.Policy.Minimum))
        self.bottomLayout.addWidget(self.musicTimeTotal)
        self.rightLayout.addLayout(self.bottomLayout)
        self._layout.addLayout(self.rightLayout)
    
    def showDetails(self):
        if self._isShowingDetails:
            return
        self.musicTitle.show()
        self.musicArtist.show()
        self.musicCover.show()
        self.setMaximumHeight(105)
        self.setMinimumHeight(105)
        self._isShowingDetails = True
        
    def hideDetails(self):
        if not self._isShowingDetails:
            return
        self.musicTitle.hide()
        self.musicArtist.hide()
        self.musicCover.hide()
        self.setMaximumHeight(55)
        self.setMinimumHeight(55)
        self._isShowingDetails = False
        
    def setMediaInfo(self, musicInfo: MediaInfo):
        self.musicCover.setPixmap(createRoundedPixmap(QPixmap(str(musicInfo.coverPath)), 30))
        self.musicTitle.setText(musicInfo.title)
        self.musicArtist.setText(musicInfo.artist)
        self.musicPlayProgress.setValue(0)
        self.musicTimePlayed.setText("0:00")
        self.musicTimeTotal.setText(humanizeDuration(musicInfo.lengthMs))
        self.playPauseButton.setIcon(qtawesomeIcon("fa6.circle-pause", color="#c3ccdf"))

class Pages(object):
    class HomePage(QFrame):
        def __init__(self):
            super().__init__()
            self._layout = QVBoxLayout()
            self.setLayout(self._layout)
            self.setMouseTracking(True)
            self.setupWidgets()
            
        def setupWidgets(self):
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(qtawesomeIcon('fa6s.music', color='#848fa3').pixmap(100, 100))
            
            welcome = QLabel("下午好，ymy139👋\n喝杯茶，放松一下吧☕")
            _font = self.font()
            _font.setPointSize(16)
            welcome.setFont(_font)
            welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
            welcome.setStyleSheet('color: #848fa3')
            
            self._layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            self._layout.addWidget(icon)
            self._layout.addWidget(welcome)
            self._layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    class PlayListPage(QFrame):
        
        @dataclass(frozen=True)
        class SyncButtonIcon:
            finish = qtawesomeIcon("fa5s.check-circle", color="#0f7b0f")
            syncing = qtawesomeIcon("mdi.dots-horizontal-circle", color="#7b700f")
            
        class HoverHighlightDelegate(QStyledItemDelegate):
            def __init__(self, parent=None):
                super().__init__(parent)
                self._hoveredRow = -1
                self.hoverBrush = QBrush(QColor(56, 61, 71))
            
            def setHoveredRow(self, row):
                if self._hoveredRow != row:
                    oldRow = self._hoveredRow
                    self._hoveredRow = row
                    if self.parent():
                        table: QTableWidget = self.parent() # pyright: ignore[reportAssignmentType]
                        if oldRow >= 0 and oldRow < table.rowCount():
                            for col in range(table.columnCount()):
                                table.update(table.model().index(oldRow, col))
                        if row >= 0 and row < table.rowCount():
                            for col in range(table.columnCount()):
                                table.update(table.model().index(row, col))
            
            def paint(self, 
                      painter: QPainter, 
                      option: QStyleOptionViewItem, 
                      index: QModelIndex | QPersistentModelIndex):
                originalBrush = painter.background()
                
                if index.row() == self._hoveredRow and not option.state & QStyle.StateFlag.State_Selected: # pyright: ignore[reportAttributeAccessIssue]
                    painter.fillRect(option.rect, self.hoverBrush) # pyright: ignore[reportAttributeAccessIssue]
                
                super().paint(painter, option, index)
                
                painter.setBackground(originalBrush)
            
            def editorEvent(self, 
                            event: QEvent, 
                            model: QAbstractItemModel, 
                            option: QStyleOptionViewItem, 
                            index: QModelIndex | QPersistentModelIndex,):
                if event.type() == QEvent.Type.MouseMove:
                    self.setHoveredRow(index.row())
                elif event.type() == QEvent.Type.Leave:
                    self.setHoveredRow(-1)
                    
                
                return super().editorEvent(event, model, option, index)
            
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout()
            self._layout.setContentsMargins(0, 3, 0, 5)
            self._layout.setSpacing(4)
            
            self.setLayout(self._layout)
            self.setMouseTracking(True)
            self.setupWidgets()
            self.resetColumnsWidth()
            
        def setupWidgets(self) -> None:
            topLayout = QHBoxLayout()
            
            self.songCount = QLabel("当前列表中有 0 首歌曲")
            _font = self.font()
            _font.setPointSize(10)
            self.songCount.setFont(_font)
            self.songCount.setStyleSheet("color: #c3ccdf")
            self.songCount.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            self.syncStatus = QLabel("播放列表更新中")
            _font = self.font()
            _font.setPointSize(10)
            self.syncStatus.setFont(_font)
            self.syncStatus.setStyleSheet("color: #c3ccdf")
            self.syncStatus.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.syncButton = QPushButton()
            self.syncButton.setMinimumSize(QSize(20, 20))
            self.syncButton.setMaximumSize(QSize(20, 20))
            self.syncButton.setIconSize(QSize(20, 20))
            self.syncButton.setStyleSheet("background-color: transparent")
            self.syncButton.setIcon(self.SyncButtonIcon.syncing)
            
            topLayout.addWidget(self.songCount)
            topLayout.addWidget(self.syncStatus)
            topLayout.addWidget(self.syncButton)
            
            self.progressBar = IndeterminateProgressBar(slowCoefficient=1.2)
            self.progressBar.setBarColor(QColor(93, 152, 204))
            
            self.playList = QTableWidget()
            self.playList.setColumnCount(4)
            self.playList.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.playList.setHorizontalHeaderLabels(["标题", "歌手", "专辑", "时长"])
            self.playList.verticalHeader().setVisible(False)
            self.playList.verticalScrollBar().setSingleStep(15)
            self.playList.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            self.playList.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.playList.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.playList.horizontalHeader().setHighlightSections(False)
            self.playList.verticalHeader().setHighlightSections(False)
            self.playList.setMouseTracking(True)
            self.playList.setItemDelegate(self.HoverHighlightDelegate(self.playList))
            _font = self.font()
            _font.setPointSize(10)
            self.playList.setFont(_font)
            self.playList.setStyleSheet("""
                QTableWidget{ 
                    border: 1px solid rgb(59, 64, 74);
                    border-radius: 5px;
                    outline: none;
                    gridline-color: rgb(59, 64, 74);
                }
                
                QTableWidget::item{ 
                    padding: 10px 5px;
                }
                
                QTableWidget::item:hover{
                    background-color: rgb(56, 61, 71);
                }
                
                QTableWidget::item:selected{
                    border: none;
                    border-radius: none;
                    background-color: rgb(56, 61, 71);
                }
                
                QScrollBar:vertical {
                    width: 12px;
                    margin: 0px;
                    background-color: transparent;
                    border-radius: none;
                    border-left: 1px solid rgb(59, 64, 74);
                }

                QScrollBar::handle:vertical {
                    background-color: #555555;
                    border-radius: 2px;
                    min-height: 20px;
                    margin: 3px;
                }

                QScrollBar::handle:vertical:hover {
                    background-color: #777777;
                }

                QScrollBar::handle:vertical:pressed {
                    background-color: #888888;
                }

                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                    width: 0px;
                    height: 0px;
                }

                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }""")
            
            self._layout.addLayout(topLayout)
            self._layout.addWidget(self.progressBar)
            self._layout.addWidget(self.playList)
            
        def resetColumnsWidth(self):
            # 12px is the width of scrollbar
            widgetWidth = self.width() - 12
            widths = [int(widgetWidth * 0.42), int(widgetWidth * 0.2), int(widgetWidth * 0.27), int(widgetWidth * 0.11)]
            
            for index, width in enumerate(widths):
                self.playList.setColumnWidth(index, width)
            
        def resizeEvent(self, event: QResizeEvent) -> None:
            self.resetColumnsWidth()
            return super().resizeEvent(event)
        
    class MusicDetailPage(QFrame):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QHBoxLayout()
            
            self.setLayout(self._layout)
            self.setMouseTracking(True)
            self.setupWidgets()
            
        def setupWidgets(self) -> None:
            rightLayout = QVBoxLayout()
            
            # TODO: Cover Size add to config
            self._coverSize = QSize(250, 250)
            self.cover = QLabel()
            self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.cover.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            self.cover.setPixmap(createRoundedPixmap(QPixmap("res/imgs/defaultCover.png"), 30, self._coverSize))
            
            self.title = QLabel("Title")
            self.title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            _font = self.font()
            _font.setPointSize(24)
            _font.setBold(True)
            self.title.setFont(_font)
            self.title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.title.setStyleSheet("color: #c3ccdf")
            
            self.artist = QLabel("Artist")
            self.artist.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            _font = self.font()
            _font.setPointSize(16)
            self.artist.setFont(_font)
            self.artist.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.artist.setStyleSheet("color: #c3ccdf")
            
            self.album = QLabel("Album")
            self.album.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            _font = self.font()
            _font.setPointSize(16)
            self.album.setFont(_font)
            self.album.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.album.setStyleSheet("color: #c3ccdf")
            
            self.lyricDisplayer = LyricWidget()
            self.lyricDisplayer.setStyleSheet("""
                QWebEngineView {
                    border: none;
                    background-color: rgb(44, 49, 60);
                }""")
            
            rightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            rightLayout.addWidget(self.cover)
            rightLayout.addWidget(self.title)
            rightLayout.addWidget(self.artist)
            rightLayout.addWidget(self.album)
            rightLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
            self._layout.addLayout(rightLayout)
            self._layout.setStretchFactor(rightLayout, 1)
            self._layout.addWidget(self.lyricDisplayer)
            self._layout.setStretchFactor(self.lyricDisplayer, 1)
            
        def setMediaInfo(self, info: MediaInfo):
            self.title.setText(info.title)
            self.album.setText(info.album)
            self.artist.setText(info.artist)
            if info.coverPath:
                self.cover.setPixmap(createRoundedPixmap(QPixmap(info.coverPath), 30, self._coverSize))
            else:
                self.cover.setPixmap(createRoundedPixmap(QPixmap("res/imgs/defaultCover.png"), 30, self._coverSize))
            if info.lyricsPath:
                with open(info.lyricsPath, "r") as file:
                    self.lyricDisplayer.setLrcContent(file.read())
            else:
                self.lyricDisplayer.setLrcContent("[00:00.000] 暂无歌词")

    class AboutPage(QScrollArea):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout()
            
            self.setLayout(self._layout)
            self.setupWidgets()
            
        def setupWidgets(self) -> None:
            title = QLabel("关于 PyMusicPlayer")
            _font = self.font()
            _font.setPointSize(24)
            _font.setBold(True)
            title.setFont(_font)
            
            subtitle = QLabel("简洁美观的专注于本地音乐的播放器")
            _font = self.font()
            _font.setPointSize(16)
            subtitle.setFont(_font)
            
            line = Line(color="#21252d")
            
            self._layout.addWidget(title)
            self._layout.addWidget(subtitle)
            self._layout.addWidget(line)
            self._layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    class SettingsPage(QScrollArea):
        def __init__(self) -> None:
            super().__init__()
            self._layout = QVBoxLayout()
            
            self.setLayout(self._layout)
            self.setupWidgets()
            
        def setupWidgets(self) -> None:
            self._layout.addWidget(QLabel("TODO"))
            self._layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
