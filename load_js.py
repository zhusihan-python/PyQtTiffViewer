# -*- coding: utf-8 -*-
import sys
import os
import json
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5 import QtGui
from PyQt5 import QtCore
from need.utils.common.logger import svt_logger
from need.utils.qutil import qtutils
from need.settings import proj_root


class RequestInterceptor(QWebEngineUrlRequestInterceptor):

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        print("interceptRequest:", url, info.requestMethod())


source_data = """'E:/projects/qt_practice/OpenSeaDragonDemo/GeneratedImages/target_files/',"""
first_half = """    var viewer = OpenSeadragon({{
        id:'openseadragon1',
        prefixUrl: '{root}/static/images/',
        showNavigator: '1',
        showRotationControl: '1',
        showFlipControl: '1',
        navigatorSizeRatio: '0.2',
        navigatorMaintainSizeRatio: '1',
        navigatorBackground: 'transparent',
        navigatorBorderColor: 'transparent',
        fullPage: '1',
        // fullPageButton: 'vFullScreen',
        tileSources: {{
        Image: {{
            xmlns:  'http://schemas.microsoft.com/deepzoom/2009',
            Url: """.format(root=proj_root)
last_half = """
            Overlap: '1',
            TileSize: '128',
            Format : 'jpeg',
            Size:{{
                Height: '{height}',
                Width:  '{width}',
               }}
            }}  
        }}
    }});
    viewer.canvas.addEventListener('contextmenu', function(event) {{
        event.preventDefault();
    }});
    viewer.scalebar({{
        type: OpenSeadragon.ScalebarType.MAP,
        pixelsPerMeter: 1e7,
        minWidth: "75px",
        location: OpenSeadragon.ScalebarLocation.BOTTOM_LEFT,
        xOffset: 5,
        yOffset: 10,
        stayInsideImage: true,
        color: "rgb(150, 150, 150)",
        fontColor: "rgb(100, 100, 100)",
        backgroundColor: "rgba(255, 255, 255, 0.5)",
        fontSize: "small",
        barThickness: 2
    }});
"""

script = first_half + source_data + last_half


class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)
        svt_logger.info("javaScriptConsoleMessage: ", level, message, lineNumber)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        # self.dockWidget = QDockWidget()
        # self.dockWidget.DockWidgetClosable = 0
        self.setWindowTitle("切片浏览")
        self.form_widget = FormWidget(self)
        # _widget = QWidget()
        _layout = QHBoxLayout()
        _layout.addWidget(self.form_widget)
        self.setLayout(_layout)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.form_widget.sizePolicy().hasHeightForWidth())
        self.form_widget.setSizePolicy(sizePolicy)
        self.form_widget.setMinimumSize(QtCore.QSize(1200, 800))
        # self.form_widget.setMaximumSize(QtCore.QSize(1800, 1760))
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setWindowTitle("切片浏览")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/image_view.png"))
        self.setWindowIcon(icon)
        self.script = ""
        self.__controls()
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        self.setLayout(vbox)
        # self.__layout()

    def __controls(self):
        html_path = proj_root + r"/static/index.html"
        html = open(html_path, 'r', encoding='UTF-8').read()
        # print("html", html)
        self.browser = QWebEngineView()
        # self.browser.page().profile().defaultProfile().setRequestInterceptor(RequestInterceptor(self))

        self.browser.setPage(WebEnginePage(self.browser))
        self.browser.setHtml(html)
        self.browser.setHtml(html, QtCore.QUrl.fromLocalFile(os.path.dirname(os.path.realpath(__file__))))
        # self.browser.load(QtCore.QUrl.fromLocalFile(os.path.abspath("index.html")))
        self.browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.browser.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        # self.browser.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        # self.browser.page().fullScreenRequested.connect(
        #     lambda request, browser=self.browser: self.handle_fullscreen_requested(
        #         request, browser
        #     )
        # )
        self.browser.loadFinished.connect(self.onLoadFinished)

    def onLoadFinished(self, ok):
        if ok:
            self.browser.page().runJavaScript(self.script, self.ready)

    @pyqtSlot(str)
    def reload(self, source):
        image_info_path = "/".join(source[1:].split("/")[:-2]) + "/info.json"
        print("image_info_path", image_info_path)
        if not os.path.exists(image_info_path):
            return
        with open(image_info_path) as f:
            image_info = json.load(f)
            img_width = image_info.get("width")
            img_height = image_info.get("height")
        input_script = first_half + source + last_half.format(width=img_width, height=img_height)
        # print("full input_script", input_script)
        if self.script != input_script:
            self.script = input_script
            # print("self.script in reload", self.script)
            # self.browser.page().runJavaScript(script, self.ready)
            self.browser.reload()

    def __layout(self):
        # self.vbox = QVBoxLayout()
        self.hBox = QVBoxLayout()
        self.hBox.addWidget(self.browser)
        # self.vbox.addLayout(self.hBox)
        self.setLayout(self.hBox)

    def ready(self, returnValue):
        print(returnValue)
        self.browser.page().runJavaScript("viewer.setFullPage(!0);")

    def handle_fullscreen_requested(self, request, browser):
        request.accept()
        print("request.toggleOn()", request.toggleOn())
        if request.toggleOn():
            self.showMaximized()

    def changeEvent(self, e):
        # print("e in changeEvent", e.type())
        # print("window state in changeEvent", int(self.windowState()))
        if e.type() == QEvent.WindowStateChange:
            self.browser.page().runJavaScript("viewer.fullPageButton.onRelease()", self.ready)
            # if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
            #     self.showMaximized()
                # self.browser.page().runJavaScript("viewer.setFullPage(!0);")
        super().changeEvent(e)


def main():
    # os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "8888"
    app = QApplication(sys.argv)
    windowGeometry = app.desktop().availableGeometry(0)
    print("windowGeometry", windowGeometry)

    # win = MainWindow()
    # win.setMinimumSize(1700, 1600)
    # win.show()
    # widget = win.form_widget
    # widget.move(windowGeometry.topLeft())
    # widget.resize(windowGeometry.size())
    # loop = QEventLoop()
    # QTimer.singleShot(2000, loop.quit)
    # loop.exec_()
    # win.form_widget.reload("""'E:/data/20211212_18/target/target_files/',""")
    #
    # win2 = MainWindow()
    # # win.setMinimumSize(1700, 1600)
    # win2.show()
    # widget = win2.form_widget
    # widget.move(windowGeometry.topLeft())
    # widget.resize(windowGeometry.size())
    # loop = QEventLoop()
    # QTimer.singleShot(2000, loop.quit)
    # loop.exec_()
    # win2.form_widget.reload("""'E:/projects/NeatSvtScanRefa/data/20211221_27/target/target_files/',""")
    form_widget = FormWidget()
    form_widget.setMinimumSize(1200, 1000)
    form_widget.reload("""'E:/projects/NeatSvtScan/data/20220301_28/target/target_files/',""")
    form_widget.show()

    # dw = QWebEngineView()
    # dw.setWindowTitle('开发人员工具')
    # dw.load(QtCore.QUrl('http://127.0.0.1:8888'))
    # dw.move(600, 100)
    # dw.show()

    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
