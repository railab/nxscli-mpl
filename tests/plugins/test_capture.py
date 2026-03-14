import numpy as np
from nxslib.dev import DeviceChannel
from nxslib.nxscope import DNxscopeStreamBlock

from nxscli_mpl.plot_mpl import PlotDataCommon
from nxscli_mpl.plugins.capture import PluginCapture


def test_plugincapture_init():
    plugin = PluginCapture()

    assert plugin.stream is True

    # TODO:


def test_plugincapture_handle_blocks_updates_datalen() -> None:
    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")

    class DummyPlot:
        def __init__(self) -> None:
            self.plist = [PlotDataCommon(chan)]

    plugin = PluginCapture()
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

    plugin = PluginCapture()
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

    plugin = PluginCapture()
    plugin._plot = DummyPlot()
    plugin._write = ""

    out = plugin.result()

    assert out is plugin._plot
