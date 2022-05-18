# -*- coding: utf-8 -*-
import sys
import os
import json
from django.http import HttpResponse

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlSchemeHandler
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import pyqtSlot, QEvent, QObject, QByteArray, QBuffer, QIODevice
from PyQt5 import QtGui
from PyQt5 import QtCore

from open_tiff import source


BASE_DIR = os.path.dirname(__file__)


class RequestInterceptor(QWebEngineUrlRequestInterceptor):

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        print("interceptRequest:", url, info.requestMethod())
        if url.endswith("thumbnail.png"):
            print("interceptRequest get thumbnail.png:", url, info.navigationType())


class UrlSchemeHandler(QWebEngineUrlSchemeHandler):

    def requestStarted(self, job):
        url = job.requestUrl().toString()
        print("requestStarted in UrlSchemeHandler", url)
        if url.endswith("thumbnail.png"):
            # file = QFile('Data/app.png', job)
            # file.open(QIODevice.ReadOnly)
            # job.reply(b'image/png', file)
            print("requestStarted get thumbnail.png:", url)


class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
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


class Bridge(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

    @QtCore.pyqtSlot(int, result=str)
    def get_bands(self, idx):
        print("step into Bridge get_bands", idx)
        band_infos = source.getBandInformation()
        print("band_infos return", json.dumps(band_infos))
        return json.dumps(band_infos)

    @pyqtSlot(result=str)
    def get_color_maps(self):
        simple = {
            'red': ['#000', '#f00'],
            'r': ['#000', '#f00'],
            'green': ['#000', '#0f0'],
            'g': ['#000', '#0f0'],
            'blue': ['#000', '#00f'],
            'b': ['#000', '#00f'],
        }
        cmaps = {}
        try:
            import matplotlib.pyplot

            cmaps['matplotlib'] = list(matplotlib.pyplot.colormaps())
        except ImportError:  # pragma: no cover
            raise Exception('Install matplotlib for additional colormap choices.')
        cmaps['simple'] = [s for s in simple.keys() if len(s) > 1]

        return json.dumps(cmaps)

    @pyqtSlot(result=str)
    def get_metadata(self):
        metadata = source.getMetadata()
        return json.dumps(metadata)

    @pyqtSlot(result=QByteArray)
    def get_thumbnail(self):
        print("get into get_thumbnail")
        encoding = 'PNG'
        width = 256
        height = 256
        thumb_data, mime_type = source.getThumbnail(encoding=encoding, width=width, height=height)
        # buf = QBuffer()
        # buf.open(QIODevice.WriteOnly)
        # buf.write(thumb_data)
        # buf.seek(0)
        # buf.close()
        # print("get_thumbnail thumb_data before return", type(buf), buf.size())
        return QByteArray(thumb_data).toBase64()

    @pyqtSlot(int, int, int, result=QByteArray)
    def get_tile(self, x, y, z):
        print("into get_tiles", x, y, z)
        tile_data = source.getTile(x, y, z)
        res = QByteArray(tile_data).toBase64()

        return res

    @QtCore.pyqtSlot(int, result=int)
    def getRef(self, x):
        print("inside getRef", x)
        return x + 5

    @QtCore.pyqtSlot(int)
    def printRef(self, ref):
        print("inside printRef", ref)


class FormWidget(QWidget):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setWindowTitle("切片浏览")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/image_view.png"))
        self.setWindowIcon(icon)
        self.script = ""
        self._script = open('static/qwebchannel.js', 'rb').read().decode()
        self.bridge = Bridge(self)
        # self.channel.registerObject('Bridge', self)
        self.__controls()
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        self.setLayout(vbox)
        # self.__layout()

    def __controls(self):
        html_path = BASE_DIR + r"/static/index.html"
        html = open(html_path, 'r', encoding='UTF-8').read()
        self.browser = QWebEngineView()
        # self.browser.setPage(WebEnginePage(self.browser))
        self.browser.page().profile().defaultProfile().setRequestInterceptor(RequestInterceptor(self))
        self.browser.page().profile().defaultProfile().installUrlSchemeHandler(b'', UrlSchemeHandler(self.browser))
        self.channel = QWebChannel(self.browser.page())

        self.browser.page().setWebChannel(self.channel)
        self.channel.registerObject('Bridge', self.bridge)

        # self.browser.setHtml(html)
        # self.browser.setHtml(html, QtCore.QUrl.fromLocalFile(os.path.dirname(os.path.realpath(__file__))))
        self.browser.load(QtCore.QUrl.fromLocalFile(os.path.abspath(html_path)))
        self.browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.browser.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        # self.browser.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    #     self.browser.page().loadFinished.connect(self.onLoadFinished)
    #
    # def onLoadFinished(self, ok):
    #     if ok:
    #         self.browser.page().runJavaScript(self._script)

    @pyqtSlot()
    def get_metadata(self):
        print("get_metadata")

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
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "8888"
    app = QApplication(sys.argv)

    form_widget = FormWidget()
    form_widget.setMinimumSize(1200, 1000)
    # form_widget.reload("""'E:/projects/NeatSvtScan/data/20220301_28/target/target_files/',""")
    form_widget.show()

    dw = QWebEngineView()
    dw.setWindowTitle('devtools')
    dw.load(QtCore.QUrl('http://127.0.0.1:8888'))
    dw.move(600, 100)
    dw.show()

    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
