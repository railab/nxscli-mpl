"""Module containing animation1 plugin."""

from typing import TYPE_CHECKING, Any

from nxscli_mpl.animation_mpl import IPluginAnimation
from nxscli_mpl.plot_mpl import PlotDataAxesMpl, PluginAnimationCommonMpl

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    from nxscli.idata import PluginQueueData


###############################################################################
# Class: Animation1
###############################################################################


class LiveAnimation(PluginAnimationCommonMpl):
    """Infinity animation with x axis extension."""

    def __init__(
        self,
        fig: "Figure",
        pdata: PlotDataAxesMpl,
        qdata: "PluginQueueData",
        write: str,
        hold_after_trigger: bool = False,
        hold_post_samples: int = 0,
    ) -> None:
        """Initialzie an animtaion1 handler.

        :param fig: matplotlib Figure
        :param pdata: axes handler
        :param qdata: stream queue handler
        :param write: write path
        """
        PluginAnimationCommonMpl.__init__(
            self,
            fig,
            pdata,
            qdata,
            write,
            hold_after_trigger=hold_after_trigger,
            hold_post_samples=hold_post_samples,
        )

    def _animation_update(
        self,
        frame: tuple[list[Any], list[Any], float | None],
        pdata: PlotDataAxesMpl,
        trigger_x: float | None = None,
    ) -> list["Line2D"]:  # pragma: no cover
        """Update an animation with dynamic scaling."""
        del trigger_x
        # update sample
        pdata.xdata_extend(frame[0])
        pdata.ydata_extend(frame[1])
        if frame[2] is not None or not self._hold_after_trigger:
            pdata.set_trigger_marker(frame[2])

        # update y scale
        self.yscale_extend(frame[1], pdata)

        # update x scale
        self.xscale_extend(frame[0], pdata)

        # set new data
        i = 0
        for ln in pdata.lns:
            ln.set_data(pdata.xdata[i], pdata.ydata[i])
            i += 1
        if pdata.trigger_x is not None:
            pdata.trigger_line.set_xdata([pdata.trigger_x, pdata.trigger_x])
            pdata.trigger_line.set_visible(True)
        else:
            pdata.trigger_line.set_visible(False)

        return pdata.lns + [pdata.trigger_line]


###############################################################################
# Class: PluginLive
###############################################################################


class PluginLive(IPluginAnimation):
    """Infinity animation with x axis extension."""

    def __init__(self) -> None:
        """Initialize an animation1 plugin."""
        IPluginAnimation.__init__(self)

    def _start(
        self,
        fig: "Figure",
        pdata: PlotDataAxesMpl,
        qdata: "PluginQueueData",
        kwargs: Any,
    ) -> PluginAnimationCommonMpl:
        """Start an animation1 plugin."""
        return LiveAnimation(
            fig,
            pdata,
            qdata,
            kwargs["write"],
            hold_after_trigger=kwargs.get("hold_after_trigger", False),
            hold_post_samples=kwargs.get("hold_post_samples", 0),
        )
