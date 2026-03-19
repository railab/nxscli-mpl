import numpy as np
from nxslib.dev import DeviceChannel
from nxslib.nxscope import DNxscopeStreamBlock

from nxscli_mpl.plot_mpl import PlotDataCommon
from nxscli_mpl.plugins.snap import PluginSnap


def test_plugincapture_init():
    plugin = PluginSnap()

    assert plugin.stream is True
    assert plugin.get_plot_handler() is None


def test_plugincapture_init_hook_accepts_connected_handler() -> None:
    plugin = PluginSnap()
    plugin.connect_phandler(object())
    plugin._init()


def test_plugincapture_handle_blocks_updates_datalen() -> None:
    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")

    class DummyPlot:
        def __init__(self) -> None:
            self.plist = [PlotDataCommon(chan)]

    plugin = PluginSnap()
    plugin._plot = DummyPlot()
    plugin._datalen = [0]
    pdata = type("Q", (), {"vdim": 2})()
    plugin._handle_blocks(
        [
            DNxscopeStreamBlock(
                data=np.array([[1.0, 2.0], [3.0, 4.0]]),
                meta=None,
            )
        ],
        pdata,
        0,
    )
    assert plugin._plot.plist[0].ydata == [[1.0, 3.0], [2.0, 4.0]]
    assert plugin._datalen[0] == 2


def test_plugincapture_thread_common_numpy_path() -> None:
    class DummyThread:
        def __init__(self) -> None:
            self.stopped = False

        def stop_set(self) -> None:
            self.stopped = True

    class DummyQData:
        vdim = 1

        def queue_get(
            self, block: bool = True, timeout: float = 1.0
        ):  # noqa: ANN001, ARG002
            return [
                DNxscopeStreamBlock(data=np.array([[1.0], [2.0]]), meta=None)
            ]

    chan = DeviceChannel(chan=0, _type=2, vdim=1, name="chan0")

    class DummyPlot:
        def __init__(self) -> None:
            self.plist = [PlotDataCommon(chan)]
            self.qdlist = [DummyQData()]

    plugin = PluginSnap()
    plugin._plot = DummyPlot()
    plugin._plugindata = plugin._plot
    plugin._datalen = [0]
    plugin._samples = 2
    plugin._nostop = False
    plugin._thread = DummyThread()
    plugin._thread_common()
    assert plugin._datalen[0] == 2
    assert plugin._thread.stopped is True


def test_plugincapture_result_attached_mode_skips_show() -> None:
    class DummyPlotData:
        def plot(self) -> None:
            return

    class DummyPlot:
        def __init__(self) -> None:
            self.mode = "attached"
            self.plist = [DummyPlotData()]
            self.fig = None

    plugin = PluginSnap()
    plugin._plot = DummyPlot()
    plugin._write = ""

    assert plugin.get_plot_handler() is plugin._plot

    out = plugin.result()

    assert out is plugin._plot


def test_plugincapture_result_detached_shows_figure_and_finalizes(
    mocker,
) -> None:
    class DummyPlotData:
        def __init__(self) -> None:
            self.plotted = False

        def plot(self) -> None:
            self.plotted = True

    class DummyPlot:
        def __init__(self) -> None:
            self.mode = "detached"
            self.plist = [DummyPlotData()]
            self.fig = None

    plugin = PluginSnap()
    plugin._plot = DummyPlot()
    plugin._write = ""
    show = mocker.patch("nxscli_mpl.plugins.snap.MplManager.show")
    info = mocker.patch("nxscli_mpl.plugins.snap.logger.info")

    out = plugin.result()
    plugin._final()

    assert out is plugin._plot
    assert plugin._plot.plist[0].plotted is True
    show.assert_called_once_with(block=False)
    info.assert_called_once_with("plot capture DONE")


def test_plugincapture_start_uses_build_plot_surface(mocker) -> None:
    class DummyPlotData:
        def __init__(self) -> None:
            self.xlim = None

        def set_xlim(self, xlim) -> None:
            self.xlim = xlim

    class DummyPlot:
        def __init__(self) -> None:
            self.plist = [DummyPlotData()]
            self.qdlist = [object()]

    plugin = PluginSnap()
    plugin.connect_phandler(object())
    plot = DummyPlot()
    build = mocker.patch(
        "nxscli_mpl.plugins.snap.build_plot_surface", return_value=plot
    )
    thread_start = mocker.patch.object(plugin, "thread_start")

    out = plugin.start(
        {
            "samples": 8,
            "write": "snap.png",
            "nostop": True,
            "channels": [1],
            "trig": [],
            "dpi": 100,
            "fmt": [""],
        }
    )

    assert out is True
    build.assert_called_once_with(plugin._phandler, mocker.ANY)
    thread_start.assert_called_once_with(plot)
    assert plugin._write == "snap.png"
    assert plot.plist[0].xlim == (0, 8)
