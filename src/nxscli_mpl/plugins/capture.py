"""Module containing capture plugin."""

from typing import TYPE_CHECKING, Any

from nxscli.iplugin import IPluginPlotStatic
from nxscli.logger import logger
from nxscli.pluginthr import PluginThread

from nxscli_mpl.plot_mpl import MplManager, PluginPlotMpl

if TYPE_CHECKING:
    from nxscli.idata import PluginQueueData
    from nxslib.nxscope import DNxscopeStream


###############################################################################
# Class: PluginCapture
###############################################################################


class PluginCapture(PluginThread, IPluginPlotStatic):
    """Plugin that plot static captured data."""

    def __init__(self) -> None:
        """Intiialize a capture plot plugin."""
        IPluginPlotStatic.__init__(self)
        PluginThread.__init__(self)

        self._plot: "PluginPlotMpl"
        self._write: str

    def _init(self) -> None:
        assert self._phandler

    def _final(self) -> None:
        logger.info("plot capture DONE")

    def _handle_samples(
        self, data: list["DNxscopeStream"], pdata: "PluginQueueData", j: int
    ) -> None:
        # store data
        ydata: list[list[Any]] = [[] for v in range(pdata.vdim)]
        for sample in data:
            for i in range(pdata.vdim):
                # TODO: metadata not supported for now
                ydata[i].append(sample.data[i])

        # extend ydata
        self._plot.plist[j].ydata_extend(ydata)
        # get data len
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

        chanlist = self._phandler.chanlist_plugin(kwargs["channels"])
        trig = self._phandler.triggers_plugin(chanlist, kwargs["trig"])

        cb = self._phandler.cb_get()
        self._plot = PluginPlotMpl(
            chanlist, trig, cb, dpi=kwargs["dpi"], fmt=kwargs["fmt"]
        )

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

        MplManager.show(block=False)
        return self._plot
