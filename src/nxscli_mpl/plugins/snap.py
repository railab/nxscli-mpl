"""Module containing capture plugin."""

from typing import TYPE_CHECKING, Any

import numpy as np
from nxscli.iplugin import IPluginPlotStatic
from nxscli.logger import logger
from nxscli.pluginthr import PluginThread

from nxscli_mpl.plot_mpl import (
    MplManager,
    PluginPlotMpl,
    build_plot_surface,
)

if TYPE_CHECKING:
    from nxscli.idata import PluginQueueData
    from nxslib.nxscope import DNxscopeStreamBlock


###############################################################################
# Class: PluginSnap
###############################################################################


class PluginSnap(PluginThread, IPluginPlotStatic):
    """Plugin that plot static captured data."""

    def __init__(self) -> None:
        """Intiialize a capture plot plugin."""
        IPluginPlotStatic.__init__(self)
        PluginThread.__init__(self)

        self._plot: "PluginPlotMpl"
        self._write: str

    def get_plot_handler(self) -> "PluginPlotMpl | None":
        """Return the matplotlib plot handler.

        :return: PluginPlotMpl instance, or None if start() has not been called
        """
        return getattr(self, "_plot", None)

    def _init(self) -> None:
        assert self._phandler

    def _final(self) -> None:
        logger.info("plot capture DONE")

    def _handle_blocks(
        self,
        data: list["DNxscopeStreamBlock"],
        pdata: "PluginQueueData",
        j: int,
    ) -> None:
        ydata: list[list[Any]] = [[] for _ in range(pdata.vdim)]
        for block in data:
            block_data = block.data
            assert isinstance(block_data, np.ndarray)
            if int(block_data.shape[0]) == 0:  # pragma: no cover
                continue
            for i in range(pdata.vdim):
                ydata[i].extend(block_data[:, i])

        self._plot.plist[j].ydata_extend(ydata)
        self._datalen[j] = len(self._plot.plist[j].ydata[0])

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
        assert self._phandler

        logger.info("start capture %s", str(kwargs))

        self._samples = kwargs["samples"]
        self._write = kwargs["write"]
        self._nostop = kwargs["nostop"]

        self._plot = build_plot_surface(self._phandler, kwargs)

        if not self._plot.qdlist or not self._plot.plist:  # pragma: no cover
            return False

        for pdata in self._plot.plist:
            # update xlim to fit our data
            if self._samples:
                pdata.set_xlim((0, self._samples))
            else:  # pragma: no cover
                pass

        self.thread_start(self._plot)

        return True

    def result(self) -> "PluginPlotMpl":
        """Get capture plugin result."""
        assert self._plot

        # plot all data
        for pdata in self._plot.plist:
            pdata.plot()

        if self._write:  # pragma: no cover
            self._plot.fig.savefig(self._write)

        if self._plot.mode == "detached":
            MplManager.show(block=False)
        return self._plot
