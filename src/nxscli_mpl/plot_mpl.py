"""The matplotlib plot specific module."""

from functools import partial
from typing import TYPE_CHECKING, Any, Generator

from matplotlib.animation import FFMpegWriter, PillowWriter
from nxscli.idata import PluginData, PluginDataCb, PluginQueueData
from nxscli.logger import logger

from nxscli_mpl._animation_common import fetch_animation_frame
from nxscli_mpl._animation_lifecycle import (
    setup_writer,
    start_animation,
    stop_animation,
    update_animation_common,
)
from nxscli_mpl._mpl_manager import MplManager
from nxscli_mpl._plot_api import EPlotMode, PlotVectorState
from nxscli_mpl._plot_constants import DEFAULT_DPI
from nxscli_mpl._plot_data import PlotDataAxesMpl, PlotDataCommon
from nxscli_mpl._plot_factory import create_plot_surface
from nxscli_mpl._plot_lifecycle import (
    attached_canvas_widget,
)
from nxscli_mpl._plot_lifecycle import (
    clear_animations as clear_plot_animations,
)
from nxscli_mpl._plot_lifecycle import (
    clear_plot_data,
    close_surface,
    is_qwidget,
)
from nxscli_mpl._plot_surface import (
    build_axes,
    expand_formats,
)
from nxscli_mpl._plot_surface import (
    get_vector_states as get_plot_vector_states,
)
from nxscli_mpl._plot_surface import (
    init_plot_data,
    numerical_channels,
)
from nxscli_mpl._plot_surface import (
    set_vector_visible as set_plot_vector_visible,
)

if TYPE_CHECKING:
    import numpy as np
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    from nxscli.trigger import TriggerHandler
    from nxslib.dev import DeviceChannel


__all__ = [
    "MplManager",
    "PlotDataCommon",
    "PlotDataAxesMpl",
    "PluginAnimationCommonMpl",
    "PluginPlotMpl",
    "EPlotMode",
    "PlotVectorState",
    "create_plot_surface",
    "build_plot_surface",
]


def build_plot_surface(
    phandler: Any, kwargs: dict[str, Any]
) -> "PluginPlotMpl":
    """Build plot surface from plugin handler and runtime kwargs."""
    chanlist = phandler.chanlist_plugin(kwargs["channels"])
    trig = phandler.triggers_plugin(chanlist, kwargs["trig"])
    cb = phandler.cb_get()
    return create_plot_surface(
        chanlist=chanlist,
        trig=trig,
        cb=cb,
        dpi=kwargs["dpi"],
        fmt=kwargs["fmt"],
        mode=str(kwargs.get("plot_mode", "detached")),
        parent=kwargs.get("plot_parent"),
    )


###############################################################################
# Class: PluginAnimationCommonMpl
###############################################################################


class PluginAnimationCommonMpl:
    """A class implementing a common matplotlib animation plot logic."""

    def __init__(
        self,
        fig: "Figure",
        pdata: PlotDataAxesMpl,
        qdata: PluginQueueData,
        write: str,
    ):
        """Initialize animation handler.

        :param fig: matplotlib Figure
        :param pdata: axes handler
        :param qdata: stream queue handler
        :param kwargs: implementation specific arguments
        """
        self._fig = fig
        self._sample_count = 0
        self._plot_data = pdata
        self._queue_data = qdata
        self._ani = None
        self._writer: PillowWriter | FFMpegWriter | None
        self._writer = setup_writer(self._fig, write)

    def _animation_init(self, pdata: PlotDataAxesMpl) -> list["Line2D"]:
        return pdata.lns

    def _animation_frames(
        self, qdata: PluginQueueData
    ) -> Generator[Any, None, None]:  # pragma: no cover
        xdata, ydata = self._animation_frames_blocks(qdata)
        yield xdata, ydata

    def _animation_frames_blocks(
        self, qdata: PluginQueueData
    ) -> tuple[list["np.ndarray[Any, Any]"], list["np.ndarray[Any, Any]"]]:
        xdata, ydata, self._sample_count = fetch_animation_frame(
            qdata, count=self._sample_count
        )
        return xdata, ydata

    def _animation_update(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> list["Line2D"] | None:
        pass  # pragma: no cover

    def pause(self) -> None:
        """Pause an animation."""
        if self._ani is not None:  # pragma: no cover
            self._ani.pause()

    def stop(self) -> None:  # pragma: no cover
        """Stop animation."""
        stop_animation(self._ani, self._writer)
        del self._ani

    def _animation_update_cmn(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> list["Line2D"]:  # pragma: no cover
        """Update animation common logic."""
        return update_animation_common(
            frame,
            pdata.lns,
            lambda current: self._animation_update(current, pdata),
            self._writer,
        )

    def start(self) -> None:
        """Start an animation."""
        update = partial(self._animation_update_cmn, pdata=self._plot_data)
        frames = partial(self._animation_frames, qdata=self._queue_data)
        init = partial(self._animation_init, pdata=self._plot_data)
        self._ani = start_animation(
            fig=self._fig,
            update=update,
            frames=frames,
            init=init,
        )

    def xaxis_disable(self) -> None:  # pragma: no cover
        """Hide x axis."""
        self._plot_data.xaxis_disable()

    def yscale_extend(
        self, frame: list[Any], pdata: PlotDataAxesMpl, scale: float = 1.1
    ) -> None:  # pragma: no cover
        """Extend yscale if needed with a given scale factor.

        :param frame: frame data
        :param pdata: axes handler
        :param scale: scale factor
        """
        assert pdata.ax
        ymin, ymax = pdata.ax.get_ylim()

        new_ymax = ymax
        new_ymin = ymin
        for data in frame:
            # do nothing if empty
            if len(data) == 0:
                return

            # get min/max
            ytmp = max(data)
            if ytmp > new_ymax:
                new_ymax = ytmp
            ytmp = min(data)
            if ytmp < new_ymin:
                new_ymin = ytmp

        if new_ymax > ymax:
            new_ymax = new_ymax * scale
            ymax = new_ymax  # store for ymin update
            pdata.ax.set_ylim(ymin, new_ymax)
            pdata.ax.figure.canvas.draw()
        if new_ymin < ymin:
            new_ymin = new_ymin * scale
            pdata.ax.set_ylim(new_ymin, ymax)
            pdata.ax.figure.canvas.draw()

    def xscale_extend(
        self, frame: list[Any], pdata: PlotDataAxesMpl, scale: float = 2.0
    ) -> None:  # pragma: no cover
        """Exten x axis if needed with a agiven scale factor.

        :param frame: frame data
        :param pdata: axes handler
        :param scale: scale factor
        """
        assert pdata.ax
        xmin, xmax = pdata.ax.get_xlim()

        tmax = xmax
        # get min/max
        for i in frame:
            if len(i) > 0:
                tmp = max(i)
                if tmp > tmax:
                    tmax = tmp

        # change x scale
        if tmax > xmax:
            pdata.ax.set_xlim(xmin, scale * xmax)
            pdata.ax.figure.canvas.draw()

    def xscale_saturate(
        self, _: list[Any], pdata: PlotDataAxesMpl
    ) -> None:  # pragma: no cover
        """Saturate x axis.

        :param pdata: axes handler
        """
        assert pdata.ax
        xmin, xmax = pdata.ax.get_xlim()

        # change x scale fit for xdata
        if not pdata.xdata or not pdata.xdata[0]:
            return
        new_xmin = pdata.xdata[0][0]
        new_xmax = pdata.xdata[0][-1]
        if xmin > new_xmin or xmax < new_xmax:
            pdata.ax.set_xlim(new_xmin, new_xmax)
            # TODO: revisit
            # pdata.ax.figure.canvas.draw()


###############################################################################
# Class: PluginPlotMpl
###############################################################################


class PluginPlotMpl(PluginData):
    """A class implementing matplotlib common plot handler."""

    def __init__(
        self,
        chanlist: list["DeviceChannel"],
        trig: list["TriggerHandler"],
        cb: PluginDataCb,
        dpi: float = DEFAULT_DPI,
        fmt: list[str] | None = None,
        mode: str = "detached",
        parent: Any = None,
    ):
        """Intiialize a plot handler.

        :param chanlist: a list with plugin channels
        :param cb: plugin callback to nxslib
        :param dpi: figure DPI
        :param fmt: plot format
        """
        logger.info("prepare plot %s", str(chanlist))
        newchanlist = numerical_channels(chanlist)
        assert len(newchanlist) == len(trig)

        super().__init__(newchanlist, trig, cb)

        self._mode = EPlotMode.from_text(mode)
        self._fig = MplManager.figure(dpi)
        self._ax: list[Axes] = []
        self._ani: list[PluginAnimationCommonMpl] = []
        self._widget: Any = None
        if self._mode is EPlotMode.ATTACHED:
            self._widget = self._attached_canvas_widget()

        self._fmt = expand_formats(self._chanlist, fmt)
        self._ax = build_axes(self._fig, newchanlist)
        self._plist = init_plot_data(
            self._chanlist,
            self._ax,
            self._fmt,
            PlotDataAxesMpl,
        )

    def __del__(self) -> None:
        """Close figure and clean queue handlers."""
        try:
            self.close()
        except Exception:
            pass
        super().__del__()

    @property
    def fig(self) -> "Figure":
        """Get figure handler."""
        return self._fig

    @property
    def widget(self) -> Any:
        """Get embeddable widget for attached mode."""
        return self._widget

    @property
    def mode(self) -> str:
        """Get plot mode string."""
        return self._mode.value

    @property
    def ani(self) -> list[PluginAnimationCommonMpl]:
        """Return all registered animation isntances."""
        return self._ani

    @property
    def plist(self) -> list[PlotDataAxesMpl]:
        """Get plotdata list."""
        return self._plist

    def ani_append(self, ani: PluginAnimationCommonMpl) -> None:
        """Add animation.

        :param ani: plugin animation handler
        """
        self._ani.append(ani)

    def ani_clear(self) -> None:  # pragma: no cover
        """Clear animations."""
        self._ani = clear_plot_animations(self._ani)

    def plot_clear(self) -> None:
        """Clear plot data."""
        clear_plot_data(self._ax)

    def close(self) -> None:
        """Close figure and attached widget."""
        fig = getattr(self, "_fig", None)
        if fig is not None:
            del self._fig
        self._widget = close_surface(
            fig, getattr(self, "_widget", None), MplManager.close
        )

    def _attached_canvas_widget(self) -> Any:  # pragma: no cover
        """Return a QWidget-compatible matplotlib canvas for attached mode."""
        return attached_canvas_widget(self._fig, self._is_qwidget)

    @staticmethod
    def _is_qwidget(obj: Any) -> bool:  # pragma: no cover
        return is_qwidget(obj)

    def get_vector_states(self) -> list["PlotVectorState"]:
        """Get current vector visibility state."""
        return get_plot_vector_states(self._plist, PlotVectorState)

    def set_vector_visible(
        self, channel: int, vector: int, visible: bool
    ) -> None:
        """Set vector visibility in real time."""
        set_plot_vector_visible(
            self._plist,
            channel=channel,
            vector=vector,
            visible=visible,
        )
