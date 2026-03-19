"""The matplotlib plot specific module."""

import time
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any, Generator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import _pylab_helpers
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from nxscli.idata import PluginData, PluginDataCb, PluginQueueData
from nxscli.logger import logger
from nxslib.nxscope import DNxscopeStreamBlock

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    from nxscli.trigger import TriggerHandler
    from nxslib.dev import DeviceChannel


###############################################################################
# Class: MplManager
###############################################################################


class MplManager:
    """Matplotlib global manager."""

    @staticmethod
    def draw() -> None:  # pragma: no cover
        """Draw an animation."""
        plt.draw()

    @staticmethod
    def fig_is_open() -> Any:  # pragma: no cover
        """Return a list of opened figures."""
        return plt.get_fignums()

    @staticmethod
    def pause(interval: float) -> None:  # pragma: no cover
        """Handle Matplotlib events.

        Modified pyplot.pause() without show(False) in the middle.

        :param interval: pause interval
        """
        manager = _pylab_helpers.Gcf.get_active()
        if manager is not None:
            canvas = manager.canvas
            if canvas.figure.stale:
                canvas.draw_idle()
            # show(block=False)
            canvas.start_event_loop(interval)
        else:
            time.sleep(interval)

    @staticmethod
    def show(block: bool = True) -> None:
        """Show an animation.

        :param block: blocking operation
        """
        plt.show(block=block)  # pragma: no cover

    @staticmethod
    def style_set(style: list[str]) -> None:
        """Configure matplotlib."""
        logger.info("plt.style %s", str(style))
        plt.style.use(style)

    @staticmethod
    def figure(dpi: float = 100.0) -> "Figure":
        """Get figure.

        :param dpi: figure DPI
        """
        return plt.figure(dpi=dpi)

    @staticmethod
    def func_animation(**kwargs: Any) -> Any:
        """Create animation.

        :param kwargs: animation arugments
        """
        return FuncAnimation(**kwargs)

    @staticmethod
    def close(fig: "Figure") -> None:
        """Close figure.

        :param fig: matplotlib Figure
        """
        if plt.fignum_exists(fig.number):  # pragma: no cover
            plt.close(fig)


###############################################################################
# Class: PlotDataCommon
###############################################################################


class PlotDataCommon:
    """A class implementing common plot data."""

    def __init__(self, channel: "DeviceChannel"):
        """Initialize common plot data.

        :param channel: channel instance
        """
        self._xdata: list[Any] = []
        self._ydata: list[Any] = []
        self._vdim = channel.data.vdim
        self._chan = channel.data.chan
        for _ in range(self._vdim):
            self._xdata.append([])
            self._ydata.append([])

        self._samples_max = 0

    @property
    def chan(self) -> int:
        """Get channel id."""
        return self._chan

    @property
    def xdata(self) -> list[list[Any]]:
        """Get X data."""
        return self._xdata

    @property
    def ydata(self) -> list[list[Any]]:
        """Get Y data."""
        return self._ydata

    @property
    def samples_max(self) -> int:
        """Get max samples."""
        return self._samples_max

    @samples_max.setter
    def samples_max(self, smax: int) -> None:
        """Set max samples.

        :param smax: set max num of samples
        """
        self._samples_max = smax

    def xdata_extend(self, data: list[list[Any]]) -> None:
        """Extend X data.

        :param data: X data to extend
        """
        for i, xdata in enumerate(self._xdata):
            xdata.extend(data[i])

    def ydata_extend(self, data: list[list[Any]]) -> None:
        """Extend Y data.

        :param data: Y data to extend
        """
        for i, ydata in enumerate(self._ydata):
            ydata.extend(data[i])

    def xdata_extend_max(self, data: list[list[Any]]) -> None:
        """Extend X data and saturate to a configured number of samples.

        :param data: X data to extend
        """
        for i, _ in enumerate(self._xdata):
            self._xdata[i].extend(data[i])
            remove = len(self._xdata[i]) - self._samples_max
            if remove > 0:
                self._xdata[i] = self._xdata[i][remove:]

    def ydata_extend_max(self, data: list[list[Any]]) -> None:
        """Extend Y data and saturate to a configured number of samples.

        :param data: Y data to extend
        """
        for i, _ in enumerate(self._xdata):
            self._ydata[i].extend(data[i])
            remove = len(self._ydata[i]) - self._samples_max
            if remove > 0:
                self._ydata[i] = self._ydata[i][remove:]


###############################################################################
# Class: PlotDataAxesMpl
###############################################################################


class PlotDataAxesMpl(PlotDataCommon):
    """A class implementing common matplotlib axes logic."""

    def __init__(
        self,
        ax: "Axes",
        channel: "DeviceChannel",
        fmt: list[str] | None = None,
    ):
        """Initialize matplotlib specific plot data.

        :param ax: matplotlib Axes
        :param channel: channel instance
        :param fmt: plot format
        """
        PlotDataCommon.__init__(self, channel)

        # initialize axis only if numerical channel
        if not channel.data.is_numerical:
            raise TypeError

        self._ax = ax

        if not fmt:
            # extend for all vectors
            self._fmt = ["" for _ in range(channel.data.vdim)]
        else:
            # we have to configure each vector individualy
            assert (
                len(fmt) == channel.data.vdim
            ), "fmt must match vectors in configured channel"
            self._fmt = fmt

        # we need lines for animations
        self._lns: list["Line2D"] = []
        for i in range(channel.data.vdim):
            lines = self._ax.plot([], [], self._fmt[i])
            self._lns.append(lines[0])

        # set grid
        self.grid_set(True)

        # set plot title if channel name available
        if len(channel.data.name) > 0:  # pragma: no cover
            self.plot_title = channel.data.name

    def __str__(self) -> str:
        """Format string representation."""
        _str = "PlotDataAxesMpl" + "(channel=" + str(self.chan) + ")"
        return _str

    @property
    def ax(self) -> "Axes":
        """Get axes."""
        return self._ax

    @property
    def lns(self) -> list["Line2D"]:
        """Get lines."""
        return self._lns

    @property
    def xlim(self) -> Any:
        """Get pot X limits."""
        assert self._ax
        return self._ax.get_xlim()

    @property
    def ylim(self) -> Any:
        """Get pot Y limits."""
        assert self._ax
        return self._ax.get_ylim()

    @property
    def plot_title(self) -> Any:
        """Get the plot title."""
        assert self._ax
        return self._ax.get_title()

    @plot_title.setter
    def plot_title(self, title: str) -> None:
        """Set the plot title.

        :param title: plot title
        """
        assert self._ax
        self._ax.set_title(title)

    def set_xlim(self, xlim: tuple[Any, Any]) -> None:
        """Set plot X limits.

        :param xlim: set X limits
        """
        assert self._ax
        self._ax.set_xlim(*xlim)

    def set_ylim(self, ylim: tuple[Any, Any]) -> None:
        """Set plot Y limits.

        :param ylim: set Y limits
        """
        assert self._ax
        self._ax.set_ylim(*ylim)

    def plot(self) -> None:
        """Plot all data."""
        assert self._ax
        for i, data in enumerate(self._ydata):
            self._ax.plot(data, self._fmt[i])

    def xaxis_disable(self) -> None:
        """Disable x axis ticks."""
        self.xaxis_set_ticks([])

    def xaxis_set_ticks(self, ticks: list[Any]) -> None:
        """Set ticks for X axis.

        :param ticks: set ticks for X axis
        """
        assert self._ax
        self._ax.get_xaxis().set_ticks(ticks)

    def grid_set(self, enable: bool) -> None:
        """Enable grid on plots.

        :param enable: enable or disable grid
        """
        assert self._ax
        self._ax.grid(enable)


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
        self._cnt = 0
        self._pdata = pdata
        self._qdata = qdata
        self._ani = None
        self._writer: PillowWriter | FFMpegWriter | None

        if write:  # pragma: no cover
            fps = 10
            logger.info("writer animation to file=%s, fps=%d", write, fps)

            tmp = write.split(".")
            if tmp[-1] == "gif":
                self._writer = PillowWriter(fps=fps)
            elif tmp[-1] == "mp4":
                bitrate = 200
                self._writer = FFMpegWriter(fps=fps, bitrate=bitrate)
            else:
                raise TypeError

            # NOTE: dpi arg set cause overlapping animation
            self._writer.setup(self._fig, write)
        else:
            self._writer = None

    def _animation_init(self, pdata: PlotDataAxesMpl) -> list["Line2D"]:
        return pdata.lns

    def _animation_frames(
        self, qdata: PluginQueueData
    ) -> Generator[Any, None, None]:  # pragma: no cover
        xdata, ydata = self._animation_frames_blocks(qdata)
        yield xdata, ydata

    def _animation_frames_blocks(
        self, qdata: PluginQueueData
    ) -> tuple[list[np.ndarray[Any, Any]], list[np.ndarray[Any, Any]]]:
        x_chunks: list[np.ndarray[Any, Any]] = []
        y_chunks: list[list[np.ndarray[Any, Any]]] = [
            [] for _ in range(self._qdata.vdim)
        ]

        # limit to 100 samples per frame
        for _ in range(100):
            data = qdata.queue_get(block=False)
            if not data:
                break

            if not isinstance(data, list):
                raise RuntimeError("plot animation queue payload must be list")

            for block in data:
                if not isinstance(block, DNxscopeStreamBlock):
                    raise RuntimeError(
                        "plot animation requires DNxscopeStreamBlock payload"
                    )
                block_data = block.data
                assert isinstance(block_data, np.ndarray)
                nsamples = int(block_data.shape[0])
                if nsamples == 0:
                    continue
                xr = np.arange(self._cnt, self._cnt + nsamples)
                x_chunks.append(xr)
                for i in range(self._qdata.vdim):
                    y_chunks[i].append(block_data[:, i])
                self._cnt += nsamples

        xcat = (
            np.concatenate(x_chunks)
            if x_chunks
            else np.empty((0,), dtype=np.int64)
        )
        xdata = [xcat for _ in range(self._qdata.vdim)]
        ydata = [
            (
                np.concatenate(chunks)
                if chunks
                else np.empty((0,), dtype=np.float64)
            )
            for chunks in y_chunks
        ]
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
        # TODO: stop animation
        if self._ani:
            if self._ani.event_source:
                self._ani.pause()
        if self._writer:
            self._writer.finish()

        del self._ani

    def _animation_update_cmn(
        self, frame: tuple[list[Any], list[Any]], pdata: PlotDataAxesMpl
    ) -> list["Line2D"]:  # pragma: no cover
        """Update animation common logic."""
        # no data
        if len(frame[0]) == 0 or len(frame[1]) == 0:
            return pdata.lns

        # implementation specific
        lines = self._animation_update(frame, pdata)
        assert lines

        # handle writer
        if self._writer:
            # self._fig.canvas.flush_events()
            self._writer.grab_frame()

        return lines

    def start(self) -> None:
        """Start an animation."""
        fig = self._fig
        update = partial(self._animation_update_cmn, pdata=self._pdata)
        frames = partial(self._animation_frames, qdata=self._qdata)
        init = partial(self._animation_init, pdata=self._pdata)
        self._ani = MplManager.func_animation(
            fig=fig,
            func=update,
            frames=frames,
            init_func=init,
            interval=1,
            blit=True,
            cache_frame_data=False,
        )

    def xaxis_disable(self) -> None:  # pragma: no cover
        """Hide x axis."""
        self._pdata.xaxis_disable()

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
        dpi: float = 100.0,
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
        newchanlist = []
        for chan in chanlist:
            # get only numerical channels
            if chan.data.is_numerical:
                newchanlist.append(chan)
            else:  # pragma: no cover
                logger.info(
                    "NOTE: channel %d not numerical - ignore", chan.data.chan
                )
        assert len(newchanlist) == len(trig)

        super().__init__(newchanlist, trig, cb)

        self._mode = EPlotMode.from_text(mode)
        self._fig = MplManager.figure(dpi)
        self._ax: list[Axes] = []
        self._ani: list[PluginAnimationCommonMpl] = []
        self._widget: Any = None
        if self._mode is EPlotMode.ATTACHED:
            self._widget = self._attached_canvas_widget()

        self._fmt: list[Any]
        if not fmt:
            # defaul configuration for all
            self._fmt = [None for _ in range(len(self._chanlist))]
        elif len(self._chanlist) != 1 and len(fmt) == 1:
            # the same format for all channels - extend fmt for all channels
            self._fmt = [
                [fmt[0]] * self._chanlist[i].data.vdim
                for i in range(len(self._chanlist))
            ]
        else:
            # individual fmt for all channels
            assert len(fmt) == len(
                self._chanlist
            ), "fmt must be specified for all configured channels"
            self._fmt = fmt

        # add subplots
        self._add_subplots(newchanlist)

        self._plist = self._plist_init()

    def __del__(self) -> None:
        """Close figure and clean queue handlers."""
        try:
            self.close()
        except Exception:
            pass
        super().__del__()

    def _plist_init(self) -> list[PlotDataAxesMpl]:
        ret = []
        for i, channel in enumerate(self._chanlist):
            logger.info(
                "intialize PlotDataAxesMpl chan=%d vdim=%d fmt=%s",
                channel.data.chan,
                channel.data.vdim,
                self._fmt[i],
            )
            # initialize plot
            pdata = PlotDataAxesMpl(self._ax[i], channel, fmt=self._fmt[i])
            # add plot to list
            ret.append(pdata)
        return ret

    def _add_subplots(self, channels: list["DeviceChannel"]) -> None:
        """Create subplots from channels list."""
        # remove all current axes
        for ax in self._ax:  # pragma: no cover
            if ax is not None:
                self._fig.delaxes(ax)
                # ax.remove()
            else:
                pass
        self._ax = []

        # show plots only for numerical channels
        chanlist = []
        for chan in channels:
            if chan.data.is_numerical:
                chanlist.append(chan.data.chan)
            else:  # pragma: no cover
                pass

        row = len(chanlist)
        col = 1

        i = 1
        for _ in range(len(chanlist)):
            # create subplot for all used numerical channels
            self._ax.append(self._fig.add_subplot(row, col, i))
            i += 1

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
        for ani in self._ani:
            try:
                ani.stop()
            except Exception:
                pass
        self._ani = []

    def plot_clear(self) -> None:
        """Clear plot data."""
        if len(self._ax) > 0:  # pragma: no cover
            for ax in self._ax:
                if ax is not None:
                    ax.cla()

    def close(self) -> None:
        """Close figure and attached widget."""
        fig = getattr(self, "_fig", None)
        if fig is not None:
            MplManager.close(fig)
            del self._fig

        widget = getattr(self, "_widget", None)
        if widget is not None:
            close = getattr(widget, "close", None)
            if callable(close):
                close()
            self._widget = None

    def _attached_canvas_widget(self) -> Any:  # pragma: no cover
        """Return a QWidget-compatible matplotlib canvas for attached mode."""
        canvas = getattr(self._fig, "canvas", None)
        if self._is_qwidget(canvas):
            return canvas

        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        except Exception:
            logger.warning(
                "attached matplotlib mode requires Qt canvas backend"
            )
            return None

        figure_canvas = FigureCanvasQTAgg
        return figure_canvas(self._fig)  # type: ignore[no-untyped-call]

    @staticmethod
    def _is_qwidget(obj: Any) -> bool:  # pragma: no cover
        try:
            import PyQt6.QtWidgets as QtWidgets  # type: ignore[import-not-found]  # noqa: N813,E501
        except Exception:
            return False
        return isinstance(obj, QtWidgets.QWidget)

    def get_vector_states(self) -> list["PlotVectorState"]:
        """Get current vector visibility state."""
        states: list[PlotVectorState] = []
        for pdata in self._plist:
            for vector, line in enumerate(pdata.lns):
                states.append(
                    PlotVectorState(
                        channel=pdata.chan,
                        vector=vector,
                        visible=bool(line.get_visible()),
                    )
                )
        return states

    def set_vector_visible(
        self, channel: int, vector: int, visible: bool
    ) -> None:
        """Set vector visibility in real time."""
        for pdata in self._plist:
            if pdata.chan != channel:
                continue
            if vector < 0 or vector >= len(pdata.lns):
                raise ValueError(
                    f"Invalid vector index {vector} for channel {channel}"
                )
            pdata.lns[vector].set_visible(visible)
            canvas = pdata.ax.figure.canvas
            if canvas is not None:
                draw_idle = getattr(canvas, "draw_idle", None)
                if callable(draw_idle):  # pragma: no cover
                    draw_idle()
            return
        raise ValueError(f"Channel {channel} not found")


class EPlotMode(Enum):
    """Available plot display modes."""

    DETACHED = "detached"
    ATTACHED = "attached"

    @classmethod
    def from_text(cls, value: str) -> "EPlotMode":
        """Parse mode string with safe fallback."""
        for mode in cls:
            if mode.value == value:
                return mode
        return cls.DETACHED


@dataclass(frozen=True)
class PlotVectorState:
    """Per-vector visibility state."""

    channel: int
    vector: int
    visible: bool


def create_plot_surface(
    chanlist: list["DeviceChannel"],
    trig: list["TriggerHandler"],
    cb: PluginDataCb,
    dpi: float = 100.0,
    fmt: list[str] | None = None,
    mode: str = "detached",
    parent: Any = None,
) -> PluginPlotMpl:
    """Create plot surface in detached or attached mode."""
    return PluginPlotMpl(
        chanlist=chanlist,
        trig=trig,
        cb=cb,
        dpi=dpi,
        fmt=fmt,
        mode=mode,
        parent=parent,
    )


def build_plot_surface(
    phandler: Any,
    kwargs: dict[str, Any],
) -> PluginPlotMpl:
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
