import queue

import numpy as np
import pytest  # type: ignore
from matplotlib.axes import Axes  # type: ignore
from matplotlib.figure import Figure  # type: ignore
from nxscli.idata import PluginData, PluginDataCb, PluginQueueData
from nxscli.trigger import DTriggerConfig, ETriggerType, TriggerHandler
from nxslib.dev import DeviceChannel
from nxslib.nxscope import DNxscopeStreamBlock

from nxscli_mpl.plot_mpl import (
    EPlotMode,
    MplManager,
    PlotDataAxesMpl,
    PlotDataCommon,
    PluginAnimationCommonMpl,
    PluginPlotMpl,
    build_plot_surface,
    create_plot_surface,
)
from tests.helpers import RecordingPluginHandler


def test_plotdatacommon():
    chan = DeviceChannel(0, 1, 2, "chan0")
    x = PlotDataCommon(chan)

    assert x.samples_max == 0
    x.samples_max = 100
    assert x.samples_max == 100

    assert x.xdata == [[], []]
    assert x.ydata == [[], []]

    x.xdata_extend([[1, 2], [3, 4]])
    x.ydata_extend([[5, 6], [7, 8]])
    assert x.xdata == [[1, 2], [3, 4]]
    assert x.ydata == [[5, 6], [7, 8]]
    x.xdata_extend([[9], [10]])
    x.ydata_extend([[11], [12]])
    assert x.xdata == [[1, 2, 9], [3, 4, 10]]
    assert x.ydata == [[5, 6, 11], [7, 8, 12]]

    x.samples_max = 5
    x.xdata_extend_max([[13, 14], [16, 17]])
    x.ydata_extend_max([[19, 20], [22, 23]])
    x.xdata_extend_max([[15], [18]])
    x.ydata_extend_max([[21], [24]])

    assert x.xdata == [[2, 9, 13, 14, 15], [4, 10, 16, 17, 18]]
    assert x.ydata == [[6, 11, 19, 20, 21], [8, 12, 22, 23, 24]]
    x.xdata_extend_max([[25], [26]])
    x.ydata_extend_max([[27], [28]])
    assert x.xdata == [[9, 13, 14, 15, 25], [10, 16, 17, 18, 26]]
    assert x.ydata == [[11, 19, 20, 21, 27], [12, 22, 23, 24, 28]]


def test_plotdataaxesmpl():
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))

    # not numerical channels
    chan = DeviceChannel(0, 1, 2, "chan0")
    with pytest.raises(TypeError):
        x = PlotDataAxesMpl(axes, chan)

    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")
    x = PlotDataAxesMpl(axes, chan)

    assert x.ax is axes
    assert str(x) is not None

    x.set_xlim((0, 1))
    assert x.xlim == (0, 1)
    x.set_ylim((2, 3))
    assert x.ylim == (2, 3)

    x.plot_title = "test"
    assert x.plot_title == "test"

    x.plot()
    x.xaxis_disable()
    x.xaxis_set_ticks([])

    x = PlotDataAxesMpl(axes, chan, fmt=None)
    assert x._fmt == ["", ""]

    x = PlotDataAxesMpl(axes, chan, fmt=["o", "b"])
    assert x._fmt == ["o", "b"]


def test_mplmanager_func_animation_delegates(mocker) -> None:
    fig = Figure()
    func = mocker.Mock()
    frames = mocker.Mock(return_value=iter([1]))
    create = mocker.patch(
        "nxscli_mpl.plot_mpl.FuncAnimation", return_value="ani"
    )

    out = MplManager.func_animation(fig=fig, func=func, frames=frames)

    assert out == "ani"
    create.assert_called_once_with(fig=fig, func=func, frames=frames)


def test_pluginanimationcommonmpl():
    q = queue.Queue()
    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    dtc = DTriggerConfig(ETriggerType.ALWAYS_OFF)
    qdata = PluginQueueData(q, chan, dtc)
    x = PluginAnimationCommonMpl(fig, pdata, qdata, False)

    x.stop()
    # TODO


def dummy_stream_sub(ch):
    pass


def dummy_stream_unsub(q):
    pass


def make_plot(chanlist, mode="detached", fmt=None):
    """Create a test plot with default callback and triggers."""
    dtc = DTriggerConfig(ETriggerType.ALWAYS_OFF)
    trig = [
        TriggerHandler(chan.data.chan, dtc)
        for chan in chanlist
        if chan.data.is_numerical
    ]
    cb = PluginDataCb(dummy_stream_sub, dummy_stream_unsub)
    return PluginPlotMpl(chanlist, trig, cb, mode=mode, fmt=fmt)


def test_pluginplotmpl():
    chanlist = [
        DeviceChannel(chan=0, _type=1, vdim=2, name="chan0"),  # not numerical
        DeviceChannel(chan=1, _type=2, vdim=1, name="chan1"),
        DeviceChannel(chan=2, _type=2, vdim=2, name="chan2"),
    ]
    x = make_plot(chanlist)

    assert x.fig is not None
    assert x.ani == []
    assert len(x.plist) > 0
    assert len(x._chanlist) == 2  # one channel not numerical
    assert x._fmt == [None, None]

    # test fmt configuration
    x = make_plot(chanlist, fmt="o")
    assert x._fmt == [["o"], ["o", "o"]]

    x = make_plot(chanlist, fmt=[["o"], ["b", "b"]])
    assert x._fmt == [["o"], ["b", "b"]]

    # invalid vector fmt for chan 2
    with pytest.raises(AssertionError):
        x = make_plot(chanlist, fmt=["o", "b"])
    # invalid channels fmt
    with pytest.raises(AssertionError):
        x = make_plot(chanlist, fmt=["o", "b", "c"])

    # TODO

    TriggerHandler.cls_cleanup()


def test_create_plot_surface_returns_plugin_plot() -> None:
    chanlist = [DeviceChannel(chan=1, _type=2, vdim=1, name="chan1")]
    dtc = DTriggerConfig(ETriggerType.ALWAYS_OFF)
    trig = [TriggerHandler(1, dtc)]
    cb = PluginDataCb(dummy_stream_sub, dummy_stream_unsub)

    plot = create_plot_surface(
        chanlist=chanlist,
        trig=trig,
        cb=cb,
        mode="attached",
    )

    assert isinstance(plot, PluginPlotMpl)
    assert plot.mode == EPlotMode.ATTACHED.value
    plot.close()
    TriggerHandler.cls_cleanup()


def test_pluginplotmpl_ani_clear_stops_handlers() -> None:
    """Animation cleanup should stop registered handlers before clearing."""
    chanlist = [DeviceChannel(chan=1, _type=2, vdim=1, name="chan1")]
    plot = make_plot(chanlist, mode="attached")

    class DummyAni:
        def __init__(self) -> None:
            self.stop_calls = 0

        def stop(self) -> None:
            self.stop_calls += 1

    ani1 = DummyAni()
    ani2 = DummyAni()
    plot.ani_append(ani1)  # type: ignore[arg-type]
    plot.ani_append(ani2)  # type: ignore[arg-type]

    plot.ani_clear()

    assert ani1.stop_calls == 1
    assert ani2.stop_calls == 1
    assert plot.ani == []

    plot.close()
    TriggerHandler.cls_cleanup()


def test_pluginanimationcommonmpl_init_and_start_delegate(mocker) -> None:
    q = queue.Queue()
    chan = DeviceChannel(chan=0, _type=2, vdim=1, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    dtc = DTriggerConfig(ETriggerType.ALWAYS_OFF)
    qdata = PluginQueueData(q, chan, dtc)
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    func_animation = mocker.patch.object(
        MplManager,
        "func_animation",
        return_value="animation",
    )

    assert ani._animation_init(pdata) is pdata.lns
    ani.start()

    assert ani._writer is None
    assert ani._ani == "animation"
    func_animation.assert_called_once()


def test_build_plot_surface_delegates_to_factory(mocker) -> None:
    """build_plot_surface should normalize handler callbacks once."""
    handler = RecordingPluginHandler()
    surface = object()
    create = mocker.patch(
        "nxscli_mpl.plot_mpl.create_plot_surface", return_value=surface
    )

    out = build_plot_surface(
        handler,
        {
            "channels": [1, 2],
            "trig": ["always"],
            "dpi": 123,
            "fmt": ["o"],
            "plot_mode": "attached",
            "plot_parent": "parent",
        },
    )

    assert out is surface
    create.assert_called_once_with(
        chanlist=["chan-1", "chan-2"],
        trig=[("trig", ["chan-1", "chan-2"], ["always"])],
        cb=handler.cb,
        dpi=123,
        fmt=["o"],
        mode="attached",
        parent="parent",
    )


def test_pluginanimationcommonmpl_numpy_frames():
    class FakeQueueData:
        vdim = 2

        def __init__(self) -> None:
            self._payloads = [
                [
                    DNxscopeStreamBlock(
                        data=np.array([[1.0, 2.0], [3.0, 4.0]]),
                        meta=None,
                    )
                ],
                [],
            ]

        def queue_get(self, block: bool = False):  # noqa: ANN001, ARG002
            return self._payloads.pop(0)

    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    qdata = FakeQueueData()
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    frames = ani._animation_frames(qdata)
    xdata, ydata = next(frames)
    assert [x.tolist() for x in xdata] == [[0, 1], [0, 1]]
    assert [y.tolist() for y in ydata] == [[1.0, 3.0], [2.0, 4.0]]


def test_pluginanimationcommonmpl_rejects_sample_payload() -> None:
    class FakeQueueData:
        vdim = 1

        def __init__(self) -> None:
            self._payloads = [[type("Sample", (), {"data": (7.0,)})()], []]

        def queue_get(self, block: bool = False):  # noqa: ANN001, ARG002
            if not self._payloads:
                return []
            return self._payloads.pop(0)

    chan = DeviceChannel(chan=0, _type=2, vdim=1, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    qdata = FakeQueueData()
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    with pytest.raises(RuntimeError):
        _ = next(ani._animation_frames(qdata))
    qdata._payloads = []
    assert qdata.queue_get(block=False) == []


def test_pluginanimationcommonmpl_numpy_frames_rejects_non_block() -> None:
    class BadBlock:
        data = np.array([[1.0, 2.0]])

    class FakeQueueData:
        vdim = 2

        def queue_get(self, block: bool = False):  # noqa: ANN001, ARG002
            return [BadBlock()]

    chan = DeviceChannel(chan=0, _type=2, vdim=2, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    qdata = FakeQueueData()
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    with pytest.raises(RuntimeError):
        _ = next(ani._animation_frames(qdata))


def test_pluginanimationcommonmpl_rejects_non_list_payload() -> None:
    class FakeQueueData:
        vdim = 1

        def queue_get(self, block: bool = False):  # noqa: ANN001, ARG002
            return "bad"

    chan = DeviceChannel(chan=0, _type=2, vdim=1, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    qdata = FakeQueueData()
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    with pytest.raises(RuntimeError):
        _ = next(ani._animation_frames(qdata))


def test_pluginanimationcommonmpl_numpy_frames_empty_block_and_loop_limit():
    class FakeQueueData:
        vdim = 1

        def __init__(self) -> None:
            self._n = 0

        def queue_get(self, block: bool = False):  # noqa: ANN001, ARG002
            if self._n >= 100:
                return []
            self._n += 1
            if self._n == 1:
                return [DNxscopeStreamBlock(data=np.empty((0, 1)), meta=None)]
            return [DNxscopeStreamBlock(data=np.array([[1.0]]), meta=None)]

    chan = DeviceChannel(chan=0, _type=2, vdim=1, name="chan0")
    fig = Figure()
    axes = Axes(fig, (1, 1, 2, 6))
    pdata = PlotDataAxesMpl(axes, chan)
    qdata = FakeQueueData()
    ani = PluginAnimationCommonMpl(fig, pdata, qdata, "")
    xdata, ydata = next(ani._animation_frames(qdata))
    assert len(xdata[0]) == 99
    assert len(ydata[0]) == 99
    assert qdata.queue_get(block=False) == []


def test_plot_mode_and_factory_attached():
    assert EPlotMode.from_text("attached") is EPlotMode.ATTACHED
    assert EPlotMode.from_text("invalid") is EPlotMode.DETACHED

    chanlist = [DeviceChannel(chan=1, _type=2, vdim=1, name="chan1")]
    plot = make_plot(chanlist, mode="attached")
    assert isinstance(plot, PluginPlotMpl)
    assert plot.mode == "attached"
    assert plot.widget is not None or plot.widget is None
    states = plot.get_vector_states()
    assert len(states) == 1
    plot.set_vector_visible(1, 0, False)
    with pytest.raises(ValueError):
        plot.set_vector_visible(1, 5, True)
    with pytest.raises(ValueError):
        plot.set_vector_visible(9, 0, True)
    assert plot._is_qwidget(object()) is False
    closed = {"v": False}

    class DummyWidget:
        def close(self) -> None:
            closed["v"] = True

    plot._widget = DummyWidget()
    plot.close()
    assert closed["v"] is True
    plot._widget = object()
    plot.close()
    TriggerHandler.cls_cleanup()


def test_set_vector_visible_without_canvas() -> None:
    class DummyLine:
        def __init__(self) -> None:
            self.visible = True

        def get_visible(self) -> bool:
            return self.visible

        def set_visible(self, visible: bool) -> None:
            self.visible = visible

    class DummyFigure:
        canvas = None

    class DummyAxis:
        figure = DummyFigure()

    class DummyPlotData:
        def __init__(self) -> None:
            self.chan = 5
            self.lns = [DummyLine()]
            self.ax = DummyAxis()

    plot = object.__new__(PluginPlotMpl)
    plot._plist = [DummyPlotData()]
    plot.close = lambda: None  # type: ignore[method-assign]
    plot._widget = None

    plot.set_vector_visible(5, 0, False)
    assert plot._plist[0].lns[0].get_visible() is False


def test_pluginplotmpl_del_ignores_close_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"base_del": False}

    def fake_close() -> None:
        raise RuntimeError("close failed")

    def fake_base_del(self: PluginData) -> None:
        called["base_del"] = True

    plot = object.__new__(PluginPlotMpl)
    plot.close = fake_close  # type: ignore[method-assign]
    monkeypatch.setattr(PluginData, "__del__", fake_base_del)

    PluginPlotMpl.__del__(plot)

    assert called["base_del"] is True
