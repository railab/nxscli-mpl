"""Tests for windowed plugin hooks and get_plot_handler()."""

import numpy as np
from nxslib.dev import DeviceChannel

import nxscli_mpl.plugins._typed_windowed as typed_windowed
from nxscli_mpl.plot_mpl import PlotDataCommon
from nxscli_mpl.plugins._typed_windowed import (
    PluginFftStream,
    PluginHistStream,
    PluginPolarStream,
    PluginXyStream,
    _WindowedTypedAnimation,
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
        typed_windowed, "build_plot_surface", return_value=plot
    )
    mocker.patch.object(
        typed_windowed, "_WindowedTypedAnimation", StopTrackingAni
    )
    show = mocker.patch.object(typed_windowed.MplManager, "show")

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
    show.assert_called_once_with(block=False)


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
    assert pdata.samples_max == 2


def test_xy_and_polar_plugins_init() -> None:
    assert PluginXy()._single_channel_mode is False
    polar = PluginPolar()
    assert polar._single_channel_mode is False
    assert polar._polar_ax is None
