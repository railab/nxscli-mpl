"""Module containing capture plugin."""

from typing import TYPE_CHECKING, Any

from nxscli.logger import logger

from nxscli_mpl.plot_mpl import MplManager
from nxscli_mpl.plugins._static_common import _PluginStaticBase

if TYPE_CHECKING:
    from nxscli_mpl.plot_mpl import PluginPlotMpl


###############################################################################
# Class: PluginSnap
###############################################################################


class PluginSnap(_PluginStaticBase):
    """Plugin that plot static captured data."""

    def __init__(self) -> None:
        """Intiialize a capture plot plugin."""
        super().__init__()

    def _final(self) -> None:
        logger.info("plot capture DONE")

    def wait_for_plugin(self) -> bool:  # pragma: no cover
        """Wait for figure to close."""
        done = True
        if MplManager.fig_is_open():
            done = False
            # pause
            MplManager.pause(1)
        return done

    def start(self, kwargs: Any) -> bool:
        """Start capture plugin.

        :param kwargs: implementation specific arguments
        """
        logger.info("start capture %s", str(kwargs))
        if not self._start_plot(kwargs):
            return False

        self._set_initial_xlim()

        self.thread_start(self._plot)

        return True

    def result(self) -> "PluginPlotMpl":
        """Get capture plugin result."""
        assert self._plot

        # plot all data
        for pdata in self._plot.plist:
            pdata.plot()

        self._save_plot()

        if self._plot.mode == "detached":
            MplManager.show(block=False)
        return self._plot
