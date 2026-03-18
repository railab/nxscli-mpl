"""Tests for windowed plugin hooks and get_plot_handler()."""

import nxscli_mpl.plugins._typed_windowed as typed_windowed
from nxscli_mpl.plugins._typed_windowed import (
    PluginFftStream,
    PluginHistStream,
    PluginPolarStream,
    PluginXyStream,
)
from nxscli_mpl.plugins.fft import PluginFft


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


def test_polar_windowed_get_plot_handler_after_set() -> None:
    """Test _PluginPolarWindowed.get_plot_handler() returns plot after set."""
    plugin = PluginPolarStream()

    class DummyPlot:
        pass

    plot = DummyPlot()
    plugin._plot = plot  # type: ignore[assignment]
    assert plugin.get_plot_handler() is plot
