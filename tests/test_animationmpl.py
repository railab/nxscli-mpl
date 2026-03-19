import pytest  # type: ignore

from nxscli_mpl.animation_mpl import IPluginAnimation


class DummyAni:
    def __init__(self):
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped += 1


class XTestPluginAnimation(IPluginAnimation):
    def __init__(self):
        super().__init__()

    def _start(self, fig, pdata, qdata, kwargs):
        return DummyAni()


class FakePlot:
    def __init__(self, *, mode="detached"):
        self.mode = mode
        self.fig = object()
        self.ani = []
        self.plist = [object()] if mode else []
        self.qdlist = [object()] if mode else []

    def ani_clear(self):
        self.ani = []

    def ani_append(self, ani):
        self.ani.append(ani)


class FakePluginHandler:
    pass


def test_ipluginanimation_init():
    # abstract class
    with pytest.raises(TypeError):
        IPluginAnimation()

    x = XTestPluginAnimation()

    # phandler not connected
    with pytest.raises(AttributeError):
        x.start(None)
    with pytest.raises(AttributeError):
        x.result()
    with pytest.raises(AttributeError):
        x.clear()
    with pytest.raises(AttributeError):
        x.stop()

    assert x.stream is True
    assert x.data_wait() is True
    assert x.get_plot_handler() is None

    x.connect_phandler(FakePluginHandler())


def test_ipluginanimation_start_nochannels(mocker):
    x = XTestPluginAnimation()
    x.connect_phandler(FakePluginHandler())
    mocker.patch(
        "nxscli_mpl.animation_mpl.build_plot_surface", return_value=FakePlot()
    )
    show = mocker.patch("nxscli_mpl.animation_mpl.MplManager.show")

    # start
    args = {"channels": [], "trig": [], "dpi": 100, "fmt": "", "write": False}
    assert x.start(args) is True

    # clear
    x.clear()

    # result
    x.result()
    show.assert_called_once_with(block=False)

    # stop
    x.stop()


def test_ipluginanimation_start(mocker):
    x = XTestPluginAnimation()
    x.connect_phandler(FakePluginHandler())
    plot = FakePlot()
    mocker.patch(
        "nxscli_mpl.animation_mpl.build_plot_surface", return_value=plot
    )

    # start
    args = {
        "channels": [1],
        "trig": [],
        "dpi": 100,
        "fmt": [""],
        "write": False,
    }
    assert x.start(args) is True

    # get_plot_handler returns the PluginPlotMpl after start
    assert x.get_plot_handler() is plot

    # clear
    x.clear()

    # result
    x.result()

    # stop
    x.stop()


def test_ipluginanimation_get_inputhook():
    hook = IPluginAnimation.get_inputhook()
    assert hook is not None
    hook(None)


def test_ipluginanimation_result_attached(mocker):
    x = XTestPluginAnimation()
    x.connect_phandler(FakePluginHandler())
    plot = FakePlot(mode="attached")
    mocker.patch(
        "nxscli_mpl.animation_mpl.build_plot_surface", return_value=plot
    )
    show = mocker.patch("nxscli_mpl.animation_mpl.MplManager.show")

    args = {
        "channels": [1],
        "trig": [],
        "dpi": 100,
        "fmt": [""],
        "write": False,
        "plot_mode": "attached",
    }
    assert x.start(args) is True
    ret = x.result()
    assert ret is plot
    assert ret.mode == "attached"
    show.assert_not_called()
    x.stop()
