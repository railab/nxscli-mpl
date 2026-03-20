"""Private matplotlib plot-surface helpers."""

from typing import TYPE_CHECKING, Any

from nxscli.logger import logger

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from nxslib.dev import DeviceChannel

    from nxscli_mpl._plot_api import PlotVectorState
    from nxscli_mpl._plot_data import PlotDataAxesMpl


def numerical_channels(
    chanlist: list["DeviceChannel"],
) -> list["DeviceChannel"]:
    """Return numerical channels and log ignored ones."""
    newchanlist = []
    for chan in chanlist:
        if chan.data.is_numerical:
            newchanlist.append(chan)
        else:  # pragma: no cover
            logger.info(
                "NOTE: channel %d not numerical - ignore", chan.data.chan
            )
    return newchanlist


def expand_formats(
    chanlist: list["DeviceChannel"],
    fmt: list[str] | None = None,
) -> list[Any]:
    """Expand plot format arguments for all configured channels."""
    if not fmt:
        return [None for _ in range(len(chanlist))]
    if len(chanlist) != 1 and len(fmt) == 1:
        return [[fmt[0]] * chanlist[i].data.vdim for i in range(len(chanlist))]
    assert len(fmt) == len(
        chanlist
    ), "fmt must be specified for all configured channels"
    return fmt


def build_axes(
    fig: "Figure",
    channels: list["DeviceChannel"],
) -> list["Axes"]:
    """Create subplot axes for numerical channels."""
    chan_ids = [chan.data.chan for chan in channels if chan.data.is_numerical]
    row = len(chan_ids)
    col = 1
    ret: list["Axes"] = []
    for i in range(len(chan_ids)):
        ret.append(fig.add_subplot(row, col, i + 1))
    return ret


def init_plot_data(
    chanlist: list["DeviceChannel"],
    axes: list["Axes"],
    fmt: list[Any],
    plot_data_cls: type["PlotDataAxesMpl"],
) -> list["PlotDataAxesMpl"]:
    """Create plot-data objects for each numerical channel."""
    ret = []
    for i, channel in enumerate(chanlist):
        logger.info(
            "intialize PlotDataAxesMpl chan=%d vdim=%d fmt=%s",
            channel.data.chan,
            channel.data.vdim,
            fmt[i],
        )
        ret.append(plot_data_cls(axes[i], channel, fmt=fmt[i]))
    return ret


def get_vector_states(
    plist: list["PlotDataAxesMpl"],
    state_cls: type["PlotVectorState"],
) -> list["PlotVectorState"]:
    """Return current vector visibility state for all plots."""
    states: list["PlotVectorState"] = []
    for pdata in plist:
        for vector, line in enumerate(pdata.lns):
            states.append(
                state_cls(
                    channel=pdata.chan,
                    vector=vector,
                    visible=bool(line.get_visible()),
                )
            )
    return states


def set_vector_visible(
    plist: list["PlotDataAxesMpl"],
    *,
    channel: int,
    vector: int,
    visible: bool,
) -> None:
    """Set vector visibility for a channel/vector pair."""
    for pdata in plist:
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
