import os
import sys
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel
from jinja2 import Template


class Element(QtCore.QObject):
    def __init__(self, name, parent=None):
        super(Element, self).__init__(parent)
        self._name = name

    @property
    def name(self):
        return self._name

    def script(self):
        raise NotImplementedError


class TestObject(Element):
    def script(self):
        _script = r"""
        function returnHello(){
            var i = 0;
            var id_timer = setInterval(function() { //arbitrary delay
                i++
                if(i>2){
                    {{name}}.test('gulugulu')
                }
            }, 10);
        }
        returnHello();
        """
        return Template(_script).render(name=self.name)

    @QtCore.pyqtSlot(str)
    def test(self, a):
        print(a)


class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.loadFinished.connect(self.onLoadFinished)
        self._objects = []

    def add_object(self, obj):
        self._objects.append(obj)

    @QtCore.pyqtSlot(bool)
    def onLoadFinished(self, ok):
        if ok:
            self.load_qwebchannel()
            self.load_objects()

    def load_qwebchannel(self):
        file = QtCore.QFile(":/qtwebchannel/qwebchannel.js")
        if file.open(QtCore.QIODevice.ReadOnly):
            content = file.readAll()
            file.close()
            self.runJavaScript(content.data().decode())
        if self.webChannel() is None:
            channel = QtWebChannel.QWebChannel(self)
            self.setWebChannel(channel)

    def load_objects(self):
        if self.webChannel() is not None:
            objects = {obj.name: obj for obj in self._objects}
            self.webChannel().registerObjects(objects)
            _script = r"""
            {% for obj in objects %}
            var {{obj}};
            {% endfor %}
            new QWebChannel(qt.webChannelTransport, function (channel) {
            {% for obj in objects %}
                {{obj}} = channel.objects.{{obj}};
            {% endfor %}
            }); 
            """
            self.runJavaScript(Template(_script).render(objects=objects.keys()))
            for obj in self._objects:
                if isinstance(obj, Element):
                    self.runJavaScript(obj.script())


class WebPage(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        page = WebEnginePage(self)
        self.setPage(page)

        test_object = TestObject("test_object", self)
        page.add_object(test_object)

        self.load(QtCore.QUrl("https://stackoverflow.com/"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    web = WebPage()
    web.show()
    sys.exit(app.exec_())
