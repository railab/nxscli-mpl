"""Shared windowed-plot helpers for mpl plugins."""

from typing import TYPE_CHECKING, Any

from nxscli.iplugin import IPluginPlotDynamic

from nxscli_mpl.plot_mpl import MplManager, PluginPlotMpl, build_plot_surface

if TYPE_CHECKING:
    from matplotlib.animation import FuncAnimation


class _PluginWindowedBase(IPluginPlotDynamic):
    """Common windowed-plot lifecycle for mpl plugins."""

    def __init__(self) -> None:
        super().__init__()
        self._plot: "PluginPlotMpl"

    def get_plot_handler(self) -> "PluginPlotMpl | None":
        """Return the matplotlib plot handler or None before start."""
        return getattr(self, "_plot", None)

    @property
    def stream(self) -> bool:
        return True

    def data_wait(self, timeout: float = 0.0) -> bool:
        del timeout
        return True

    def wait_for_plugin(self) -> bool:  # pragma: no cover
        done = True
        if MplManager.fig_is_open():
            done = False
            MplManager.pause(1)
        return done

    def _build_plot(self, kwargs: dict[str, Any]) -> None:
        assert self._phandler
        self._plot = build_plot_surface(self._phandler, kwargs)

    def result(self) -> "PluginPlotMpl":  # pragma: no cover
        assert self._plot
        if self._plot.mode == "detached":
            MplManager.show(block=False)
        return self._plot


class _PluginAnimationListWindowedBase(_PluginWindowedBase):
    """Windowed mpl plugins that manage plot.ani handlers."""

    def stop(self) -> None:  # pragma: no cover
        if hasattr(self, "_plot") and len(self._plot.ani) > 0:
            for ani in self._plot.ani:
                ani.stop()

    def clear(self) -> None:  # pragma: no cover
        if hasattr(self, "_plot"):
            self._plot.ani_clear()


class _PluginFuncAnimationWindowedBase(_PluginWindowedBase):
    """Windowed mpl plugins driven by FuncAnimation."""

    def __init__(self) -> None:
        super().__init__()
        self._ani: "FuncAnimation | None" = None

    def stop(self) -> None:  # pragma: no cover
        if self._ani is not None and self._ani.event_source is not None:
            self._ani.event_source.stop()
