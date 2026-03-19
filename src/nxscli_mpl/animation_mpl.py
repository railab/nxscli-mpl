"""Module containing the common matplotlib animation plugin logic."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from nxscli.iplugin import IPluginPlotDynamic
from nxscli.logger import logger

from nxscli_mpl.plot_mpl import (
    MplManager,
    PlotDataAxesMpl,
    PluginAnimationCommonMpl,
    PluginPlotMpl,
    build_plot_surface,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from nxscli.idata import PluginQueueData


###############################################################################
# Function: _create_matplotlib_inputhook
###############################################################################


def _create_matplotlib_inputhook() -> Any:  # pragma: no cover
    """Create an inputhook for matplotlib event processing.

    :return: inputhook function
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib import _pylab_helpers

        # Enable interactive mode
        plt.ion()

        def inputhook(inputhook_context: Any) -> None:
            """Process matplotlib events while waiting for input."""
            if not plt.get_fignums():
                return

            for manager in _pylab_helpers.Gcf.get_all_fig_managers():
                if manager.canvas.figure.stale:
                    manager.canvas.draw_idle()
                try:
                    manager.canvas.flush_events()
                except (NotImplementedError, AttributeError):
                    pass

        return inputhook
    except ImportError:
        return None


###############################################################################
# Class: IPluginAnimation
###############################################################################


class IPluginAnimation(IPluginPlotDynamic):
    """The common logic for an animation plugin."""

    def __init__(self) -> None:
        """Initialize an animation plugin."""
        super().__init__()

        self._plot: "PluginPlotMpl"

    @classmethod
    def get_inputhook(cls) -> Any:
        """Get matplotlib inputhook for GUI event processing.

        :return: inputhook function or None
        """
        return _create_matplotlib_inputhook()

    def get_plot_handler(self) -> "PluginPlotMpl | None":
        """Return the matplotlib plot handler.

        :return: PluginPlotMpl instance, or None if start() has not been called
        """
        return getattr(self, "_plot", None)

    @abstractmethod
    def _start(
        self,
        fig: "Figure",
        pdata: "PlotDataAxesMpl",
        qdata: "PluginQueueData",
        kwargs: Any,
    ) -> "PluginAnimationCommonMpl":
        """Abstract method.

        :param fig: matplotlib Figure
        :param pdata: axes handler
        :param qdata: stream queue handler
        :param kwargs: implementation specific arguments
        """

    @property
    def stream(self) -> bool:
        """Return True if this plugin needs stream."""
        return True

    def wait_for_plugin(self) -> bool:  # pragma: no cover
        """Wait for figure to close."""
        done = True
        if MplManager.fig_is_open():
            done = False
            # pause
            MplManager.pause(1)
        return done

    def stop(self) -> None:
        """Stop all animations."""
        assert self._plot

        if len(self._plot.ani) > 0:
            for ani in self._plot.ani:
                ani.stop()

    def clear(self) -> None:
        """Clear all animations."""
        assert self._plot

        self._plot.ani_clear()

    def data_wait(self, timeout: float = 0.0) -> bool:
        """Return True if data are ready.

        :param timeout: data wait timeout
        """
        return True

    def start(self, kwargs: Any) -> bool:
        """Start animation plugin.

        :param kwargs: implementation specific arguments
        """
        assert self._phandler

        logger.info("start %s", str(kwargs))

        self._plot = build_plot_surface(self._phandler, kwargs)

        # clear previous animations
        self.clear()

        # new animations
        for i, pdata in enumerate(self._plot.plist):
            ani = self._start(
                self._plot.fig, pdata, self._plot.qdlist[i], kwargs
            )
            self._plot.ani_append(ani)

        for ani in self._plot.ani:
            ani.start()

        return True

    def result(self) -> "PluginPlotMpl":
        """Get animation plugin result."""
        assert self._plot
        if self._plot.mode == "detached":
            MplManager.show(block=False)
        return self._plot
