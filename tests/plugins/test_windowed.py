"""Tests for windowed plugin hooks and get_plot_handler()."""

import numpy as np
from nxslib.dev import DeviceChannel
from nxslib.nxscope import DNxscopeStreamBlock

import nxscli_mpl.plugins._typed_windowed as typed_windowed
import nxscli_mpl.plugins._windowed_common as windowed_common
from nxscli_mpl.plot_mpl import PlotDataCommon
from nxscli_mpl.plugins._typed_static_strategies import get_static_strategy
from nxscli_mpl.plugins._typed_windowed import (
    PluginFftStream,
    PluginHistStream,
    PluginPolarStream,
    PluginXyStream,
    _WindowedTypedAnimation,
)
from nxscli_mpl.plugins._typed_windowed_strategies import (
    WindowedTransformState,
    get_windowed_transform_strategy,
)
from nxscli_mpl.plugins.fft import PluginFft
from nxscli_mpl.plugins.polar import PluginPolar
from nxscli_mpl.plugins.xy import PluginXy
from tests.helpers import (
    DummyStaticPlot,
    FakePlot,
    StopTrackingAni,
    make_plot_kwargs,
)


def test_windowed_get_inputhook(monkeypatch) -> None:
    """Test windowed plugins delegate get_inputhook()."""
    sentinel = object()
    monkeypatch.setattr(
        typed_windowed,
        "_create_matplotlib_inputhook",
        lambda: sentinel,
    )

    assert PluginFftStream.get_inputhook() is sentinel
    assert PluginXyStream.get_inputhook() is sentinel
    assert PluginPolarStream.get_inputhook() is sentinel


def test_typed_static_get_plot_handler() -> None:
    """Test PluginTypedStatic.get_plot_handler() before and after plot set."""
    plugin = PluginFft()
    assert plugin.get_plot_handler() is None
    plugin.connect_phandler(object())
    plugin._init()

    class DummyPlot:
        pass

    plot = DummyPlot()
    plugin._plot = plot  # type: ignore[assignment]
    assert plugin.get_plot_handler() is plot


def test_typed_windowed_get_plot_handler_before_start() -> None:
    """Test typed windowed get_plot_handler() before start."""
    plugin = PluginFftStream()
    assert plugin.get_plot_handler() is None


def test_typed_windowed_get_plot_handler_after_set() -> None:
    """Test _PluginTypedWindowed.get_plot_handler() returns plot after set."""
    plugin = PluginHistStream()

    class DummyPlot:
        pass

    plot = DummyPlot()
    plugin._plot = plot  # type: ignore[assignment]
    assert plugin.get_plot_handler() is plot


def test_xy_windowed_get_plot_handler_before_start() -> None:
    """Test _PluginXyWindowed.get_plot_handler() returns None before start."""
    plugin = PluginXyStream()
    assert plugin.get_plot_handler() is None
    assert plugin.stream is True
    assert plugin.data_wait() is True


def test_xy_windowed_get_plot_handler_after_set() -> None:
    """Test _PluginXyWindowed.get_plot_handler() returns plot after set."""
    plugin = PluginXyStream()

    class DummyPlot:
        pass

    plot = DummyPlot()
    plugin._plot = plot  # type: ignore[assignment]
    assert plugin.get_plot_handler() is plot


def test_polar_windowed_get_plot_handler_before_start() -> None:
    """Test polar windowed get_plot_handler() before start."""
    plugin = PluginPolarStream()
    assert plugin.get_plot_handler() is None
    assert plugin.stream is True
    assert plugin.data_wait() is True


def test_polar_windowed_get_plot_handler_after_set() -> None:
    """Test _PluginPolarWindowed.get_plot_handler() returns plot after set."""
    plugin = PluginPolarStream()

    class DummyPlot:
        pass

    plot = DummyPlot()
    plugin._plot = plot  # type: ignore[assignment]
    assert plugin.get_plot_handler() is plot


def test_typed_static_start_uses_build_plot_surface(mocker) -> None:
    plugin = PluginXy()
    plugin.connect_phandler(object())
    plot = DummyStaticPlot()
    build = mocker.patch(
        "nxscli_mpl.plugins._static_common.build_plot_surface",
        return_value=plot,
    )
    thread_start = mocker.patch.object(plugin, "thread_start")

    out = plugin.start(make_plot_kwargs(samples=16, nostop=False, bins=12))

    assert out is True
    build.assert_called_once_with(plugin._phandler, mocker.ANY)
    thread_start.assert_called_once_with(plot)
    assert plot.plist[0].xlim == (0, 16)


def test_typed_static_handle_blocks_updates_data_and_finalizes(
    mocker,
) -> None:
    chan = DeviceChannel(chan=1, _type=2, vdim=2, name="chan1")

    class Block:
        def __init__(self, data) -> None:
            self.data = data

    class DummyPlot:
        def __init__(self) -> None:
            self.plist = [PlotDataCommon(chan)]

    plugin = PluginFft()
    plugin._plot = DummyPlot()
    plugin._datalen = [0]
    pdata = type("Q", (), {"vdim": 2})()
    info = mocker.patch("nxscli_mpl.plugins._typed_static.logger.info")

    plugin._handle_blocks(
        [Block(np.array([[1.0, 2.0], [3.0, 4.0]]))],
        pdata,
        0,
    )
    plugin._final()

    assert plugin._plot.plist[0].ydata == [[1.0, 3.0], [2.0, 4.0]]
    assert plugin._datalen[0] == 2
    info.assert_called_once_with("plot %s DONE", plugin.plot_type)


def test_typed_windowed_start_and_result_use_common_plot_surface(
    mocker,
) -> None:
    plugin = PluginFftStream()
    plugin.connect_phandler(object())
    plot = FakePlot()
    build = mocker.patch.object(
        windowed_common, "build_plot_surface", return_value=plot
    )
    mocker.patch.object(
        typed_windowed, "_WindowedTypedAnimation", StopTrackingAni
    )
    show = mocker.patch.object(windowed_common.MplManager, "show_nonblocking")

    out = plugin.start(
        make_plot_kwargs(
            window=32,
            hop=8,
            bins=4,
            window_fn="hann",
            range_mode="auto",
        )
    )

    assert out is True
    build.assert_called_once_with(plugin._phandler, mocker.ANY)
    assert plugin.stream is True
    assert plugin.data_wait() is True
    assert len(plot.ani) == 1
    assert plot.ani[0].started == 1
    assert plugin.result() is plot
    plugin.stop()
    assert plot.ani[0].started == 0
    show.assert_called_once_with()


def test_windowed_animation_init_sets_pipeline_defaults() -> None:
    class DummyPData:
        def __init__(self) -> None:
            self.lns = [object(), object()]
            self.samples_max = 0

    pdata = DummyPData()
    ani = _WindowedTypedAnimation(
        object(),
        pdata,
        type("Q", (), {"vdim": 2})(),
        "",
        plot_type="histogram",
        window=1,
        hop=3,
        bins=0,
        window_fn="hann",
        range_mode="fixed",
    )

    assert ani._plot_type == "histogram"
    assert ani._window == 2
    assert ani._hop == 3
    assert ani._bins == 1
    assert ani._proc_names == ["curve0", "curve1"]
    assert ani._strategy is get_windowed_transform_strategy("histogram")
    assert pdata.samples_max == 2


def test_xy_and_polar_plugins_init() -> None:
    assert PluginXy()._single_channel_mode is False
    polar = PluginPolar()
    assert polar._single_channel_mode is False
    assert polar._polar_ax is None


def test_static_strategies_cover_timeseries_fft_and_xy() -> None:
    timeseries = get_static_strategy("timeseries")
    xvals, yvals = timeseries.build_xy([[1.0, 2.0]], samples=8, hist_bins=4)
    assert xvals == [[0.0, 1.0]]
    assert yvals == [[1.0, 2.0]]
    assert timeseries.render(object(), [], samples=8, hist_bins=4) is False

    fft = get_static_strategy("fft")
    xvals, yvals = fft.build_xy(
        [[1.0, 0.0, -1.0, 0.0]], samples=8, hist_bins=4
    )
    assert len(xvals) == 1
    assert len(yvals) == 1
    assert fft.render(object(), [], samples=8, hist_bins=4) is False

    xy = get_static_strategy("xy")
    xvals, yvals = xy.build_xy(
        [[1.0, 2.0], [3.0, 4.0]], samples=8, hist_bins=4
    )
    assert xvals == [[1.0, 2.0]]
    assert yvals == [[3.0, 4.0]]
    assert xy.render(object(), [], samples=8, hist_bins=4) is False
    assert get_static_strategy("unknown") is timeseries


def test_static_histogram_strategy_renders_bars() -> None:
    class DummyAxes:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def cla(self) -> None:
            self.calls.append(("cla", None))

        def bar(self, centers, counts, width, alpha) -> None:
            self.calls.append(("bar", (list(centers), list(counts), alpha)))

        def set_title(self, title: str) -> None:
            self.calls.append(("title", title))

        def relim(self) -> None:
            self.calls.append(("relim", None))

        def autoscale_view(self) -> None:
            self.calls.append(("autoscale", None))

    pdata = type("P", (), {"ax": DummyAxes()})()
    histogram = get_static_strategy("histogram")
    xvals, yvals = histogram.build_xy(
        [[1.0, 2.0, 3.0]], samples=8, hist_bins=2
    )
    assert len(xvals) == 1
    assert len(yvals) == 1
    handled = histogram.render(
        pdata,
        [[1.0, 2.0, 3.0]],
        samples=8,
        hist_bins=2,
    )
    assert handled is True
    assert [entry[0] for entry in pdata.ax.calls] == [
        "cla",
        "bar",
        "title",
        "relim",
        "autoscale",
    ]


def test_static_strategies_cover_empty_and_fallback_paths() -> None:
    fft = get_static_strategy("fft")
    xvals, yvals = fft.build_xy([[]], samples=8, hist_bins=4)
    assert xvals == [[]]
    assert yvals == [[]]

    histogram = get_static_strategy("histogram")
    xvals, yvals = histogram.build_xy([[]], samples=8, hist_bins=2)
    assert xvals == [[]]
    assert yvals == [[]]

    class DummyAxes:
        def cla(self) -> None:
            pass

        def bar(self, centers, counts, width, alpha) -> None:
            raise AssertionError("no bars expected")

        def set_title(self, title: str) -> None:
            pass

        def relim(self) -> None:
            pass

        def autoscale_view(self) -> None:
            pass

    assert histogram.render(
        type("P", (), {"ax": DummyAxes()})(),
        [[]],
        samples=8,
        hist_bins=2,
    )

    xy = get_static_strategy("xy")
    xvals, yvals = xy.build_xy([[1.0]], samples=8, hist_bins=4)
    assert xvals == [[0.0]]
    assert yvals == [[1.0]]


def test_fft_windowed_strategy_updates_lines_and_axes() -> None:
    fft = get_windowed_transform_strategy("fft")
    fft_state = WindowedTransformState()
    fft_result = fft.processor(
        np.asarray([1.0, 0.0, -1.0, 0.0], dtype=np.float64),
        bins=4,
        window_fn="hann",
        range_mode="auto",
        state=fft_state,
    )
    assert fft_result.freq.size >= 0

    class DummyLine:
        def __init__(self) -> None:
            self.data: tuple[list[float], list[float]] = ([], [])

        def set_data(self, xs, ys) -> None:  # pragma: no cover
            self.data = (list(xs), list(ys))

    class DummyAxes:
        def __init__(self) -> None:
            self.xlim = None
            self.ylim = None

        def set_xlim(self, left: float, right: float) -> None:
            self.xlim = (left, right)

        def set_ylim(self, low: float, high: float) -> None:
            self.ylim = (low, high)

    pdata = type("P", (), {"lns": [DummyLine()], "ax": DummyAxes()})()
    fft.update_plot(
        pdata,
        {"curve0": fft_result},
        proc_names=["curve0"],
        state=fft_state,
    )
    assert pdata.lns[0].data[0]
    assert pdata.ax.ylim is not None
    fft.update_plot(pdata, {}, proc_names=["curve0"], state=fft_state)


def test_hist_windowed_strategy_updates_axes_and_fixed_mode() -> None:
    histogram = get_windowed_transform_strategy("histogram")
    hist_state = WindowedTransformState()

    class DummyLine:
        def __init__(self) -> None:
            self.data: tuple[list[float], list[float]] = ([], [])

        def set_data(self, xs, ys) -> None:  # pragma: no cover
            self.data = (list(xs), list(ys))

    class DummyAxes:
        def __init__(self) -> None:
            self.xlim = None
            self.ylim = None
            self.calls: list[str] = []

        def set_xlim(self, left: float, right: float) -> None:
            self.xlim = (left, right)

        def set_ylim(self, low: float, high: float) -> None:
            self.ylim = (low, high)

        def cla(self) -> None:
            self.calls.append("cla")

        def bar(self, centers, counts, width, alpha) -> None:
            self.calls.append("bar")

        def set_title(self, title: str) -> None:
            self.calls.append(title)

    pdata = type("P", (), {"lns": [DummyLine()], "ax": DummyAxes()})()
    hist_result = histogram.processor(
        np.asarray([1.0, 2.0, 3.0, 4.0], dtype=np.float64),
        bins=2,
        window_fn="hann",
        range_mode="auto",
        state=hist_state,
    )
    histogram.update_plot(
        pdata,
        {"curve0": hist_result},
        proc_names=["curve0"],
        state=hist_state,
    )
    assert hist_state.hist_range is not None
    assert pdata.ax.calls == ["cla", "bar", "Histogram Stream"]
    histogram.processor(
        np.asarray([1.0, 2.0], dtype=np.float64),
        bins=2,
        window_fn="hann",
        range_mode="fixed",
        state=hist_state,
    )
    histogram.update_plot(pdata, {}, proc_names=["curve0"], state=hist_state)


def test_windowed_strategy_handles_empty_outputs() -> None:
    fft = get_windowed_transform_strategy("fft")
    state = WindowedTransformState(ymax_locked=2.0)
    pdata = type(
        "P",
        (),
        {
            "lns": [type("L", (), {"set_data": lambda self, xs, ys: None})()],
            "ax": type(
                "A",
                (),
                {
                    "xlim": None,
                    "ylim": None,
                    "set_xlim": lambda self, left, right: setattr(
                        self, "xlim", (left, right)
                    ),
                    "set_ylim": lambda self, low, high: setattr(
                        self, "ylim", (low, high)
                    ),
                },
            )(),
        },
    )()
    fft.update_plot(pdata, {}, proc_names=["curve0"], state=state)
    assert pdata.ax.ylim is not None


def test_windowed_common_reads_stream_blocks() -> None:
    class FakeQData:
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

        def queue_get(self, block: bool = False):  # noqa: ARG002
            return self._payloads.pop(0)

    xs, ys = windowed_common._read_channel_pair(FakeQData())

    assert xs == [1.0, 3.0]
    assert ys == [2.0, 4.0]


def test_windowed_common_reads_single_channel_values() -> None:
    class FakeQData:
        def __init__(self) -> None:
            self._payloads = [
                [
                    DNxscopeStreamBlock(
                        data=np.array([[5.0], [6.0]]), meta=None
                    )
                ],
                [],
            ]

        def queue_get(self, block: bool = False):  # noqa: ARG002
            return self._payloads.pop(0)

    assert windowed_common._read_channel_values(FakeQData()) == [5.0, 6.0]


def test_windowed_common_skips_invalid_payloads() -> None:
    class FakeQData:
        def __init__(self) -> None:
            self._payloads = [
                "bad-payload",
                [object()],
                [DNxscopeStreamBlock(data=np.empty((0, 2)), meta=None)],
                [],
            ]

        def queue_get(self, block: bool = False):  # noqa: ARG002
            return self._payloads.pop(0)

    assert windowed_common._read_channel_values(FakeQData()) == []
    assert windowed_common._read_channel_pair(FakeQData()) == ([], [])


def test_windowed_common_exhausts_drain_limit() -> None:
    class FakeQData:
        def __init__(self) -> None:
            self.calls = 0

        def queue_get(self, block: bool = False):  # noqa: ARG002
            self.calls += 1
            return [object()]

    qdata = FakeQData()

    assert windowed_common._read_channel_values(qdata) == []
    assert qdata.calls == 50

    qdata = FakeQData()
    assert windowed_common._read_channel_pair(qdata) == ([], [])
    assert qdata.calls == 50


def test_windowed_common_accumulator_applies_window_and_hop() -> None:
    acc = windowed_common._SingleChannelAccumulator(window=3, hop=2)

    assert acc.collect([], []) is None
    assert acc.collect([1.0], [2.0]) == ([1.0], [2.0])
    assert acc.collect([3.0], [4.0]) is None
    assert acc.collect([5.0], [6.0]) == ([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert acc.collect([7.0], [8.0]) is None
    assert acc.collect([9.0], [10.0]) == (
        [5.0, 7.0, 9.0],
        [6.0, 8.0, 10.0],
    )
