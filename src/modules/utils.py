from typing import Union, Literal
from pathlib import Path
import re

from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtCore import QRectF, Qt, QPoint, QSize
from PySide6.QtGui import QPixmap, QIcon, QColor

from .types_ import LrcObject

def createRoundedPixmap(pixmap: QPixmap, radius: Union[int, float], targetSize: QSize | None = None) -> QPixmap:
    if pixmap.isNull():
        return pixmap

    imageWidth = pixmap.width()
    imageHeight = pixmap.height()

    newPixmap = QPixmap(
        pixmap.scaled(imageWidth, 
                      imageWidth if imageHeight == 0 else imageHeight, 
                      Qt.AspectRatioMode.IgnoreAspectRatio,
                      Qt.TransformationMode.SmoothTransformation))
    destImage = QPixmap(imageWidth, imageHeight)
    destImage.fill(Qt.GlobalColor.transparent)

    painter = QPainter(destImage)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing | 
                          QPainter.RenderHint.SmoothPixmapTransform)

    path = QPainterPath()
    rect = QRectF(0, 0, imageWidth, imageHeight)
    path.addRoundedRect(rect, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, imageWidth, imageHeight, newPixmap)
    painter.end()
    
    if targetSize:
        destImage = destImage.scaled(targetSize, 
                                     Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)

    return destImage

def getCursorDirection(windowSize: QSize, relativePos: QPoint, contentsMargin: int) \
    -> Literal['top-left', 'top-right', 'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right'] | None:
        x, y = relativePos.x(), relativePos.y()
        width, height = windowSize.width(), windowSize.height()
        reservedArea = 2
        margin = contentsMargin - reservedArea
        
        onTop = y < margin
        onBottom = y > height - margin
        onLeft = x < margin
        onRight = x > width - margin
        
        if onTop and onLeft: return "top-left"
        elif onTop and onRight: return "top-right"
        elif onBottom and onLeft: return "bottom-left"
        elif onBottom and onRight: return "bottom-right"
        elif onTop: return "top"
        elif onBottom: return "bottom"
        elif onLeft: return "left"
        elif onRight: return "right"
        else: return None

def humanizeDuration(milliseconds: int) -> str:
    seconds = milliseconds // 1000
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def parseLrc(lrcContent: str):
    pattern = r'\[(\d+):(\d+)\.(\d+)\]'
    lines = lrcContent.strip().split('\n')
    lrcList: list[LrcObject] = []
    for line in lines:
        matches = re.findall(pattern, line)
        if matches:
            timeTags = matches
            lyric = re.sub(pattern, '', line).strip()
            for min, sec, ms in timeTags:
                totalMs = int(min) * 60000 + int(sec) * 1000 + int(ms)
                lrcList.append(LrcObject(totalMs, lyric))
    lrcList.sort(key=lambda x: x.timeMs)
    return lrcList
