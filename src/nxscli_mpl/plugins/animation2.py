"""Module containing animation2 plugin."""

from typing import TYPE_CHECKING, Any

from nxscli_mpl.animation_mpl import IPluginAnimation
from nxscli_mpl.plot_mpl import PlotDataAxesMpl, PluginAnimationCommonMpl

if TYPE_CHECKING:
    from matplotlib.figure import Figure  # type: ignore
    from matplotlib.lines import Line2D  # type: ignore
    from nxscli.idata import PluginQueueData


###############################################################################
# Class: Animation2
###############################################################################


class Animation2(PluginAnimationCommonMpl):
    """Animation with x axis saturation."""

    def __init__(
        self,
        fig: "Figure",
        pdata: PlotDataAxesMpl,
        qdata: "PluginQueueData",
        write: str,
        static_xticks: bool = True,
        disable_xaxis: bool = False,
    ):
        """Initialzie an animtaion2 handler.

        :param fig: matplotlib Figure
        :param pdata: axes handler
        :param qdata: stream queue handler
        :param write: write path
        :param static_xticks: use static X axis ticks
        :param disable_xaxis: disable X axis ticks
        """
        PluginAnimationCommonMpl.__init__(self, fig, pdata, qdata, write)

        if static_xticks is True:
            self._animation_update_priv = self._animation_update_staticx
        else:  # pragma: no cover
            self._animation_update_priv = self._animation_update_dynamicx

        if disable_xaxis is True:  # pragma: no cover
            self.xaxis_disable()

    def _animation_update(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> "Line2D":  # pragma: no cover
        return self._animation_update_priv(frame, pdata)

    def _animation_update_staticx(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> "Line2D":  # pragma: no cover
        """Update an animation with static X ticks."""
        # update sample
        pdata.xdata_extend_max(frame[0])
        pdata.ydata_extend_max(frame[1])

        # update y scale
        self.yscale_extend(frame[1], pdata)

        xdata = range(0, len(pdata.ydata[0]))
        i = 0
        for ln in pdata.lns:
            ln.set_data(xdata, pdata.ydata[i])
            i += 1

        return pdata.lns

    def _animation_update_dynamicx(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> "Line2D":  # pragma: no cover
        """Update an animation with dynamic X ticks."""
        xdata = frame[0]
        ydata = frame[1]

        if not xdata or not ydata:
            return pdata.lns

        # update sample
        pdata.xdata_extend_max(xdata)
        pdata.ydata_extend_max(ydata)

        # update y scale
        self.yscale_extend(ydata, pdata)

        # update x scale
        self.xscale_saturate(xdata, pdata)

        # set new data
        i = 0
        for ln in pdata.lns:
            ln.set_data(pdata.xdata[i], pdata.ydata[i])
            i += 1

        return pdata.lns


###############################################################################
# Class: PluginAnimation2
###############################################################################


class PluginAnimation2(IPluginAnimation):
    """Animation with x axis saturation."""

    def __init__(self) -> None:
        """Initialize an animation2 plugin."""
        IPluginAnimation.__init__(self)

    def _start(
        self,
        fig: "Figure",
        pdata: PlotDataAxesMpl,
        qdata: "PluginQueueData",
        kwargs: Any,
    ) -> PluginAnimationCommonMpl:
        """Start an animation2 plugin."""
        maxsamples = kwargs["maxsamples"]

        # configure the max number of samples
        pdata.samples_max = maxsamples
        pdata.set_xlim((0, maxsamples))

        # start animation
        return Animation2(
            fig,
            pdata,
            qdata,
            kwargs["write"],
            static_xticks=True,
            disable_xaxis=False,
        )
