"""Private matplotlib plot-data helpers."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.lines import Line2D
    from nxslib.dev import DeviceChannel


class PlotDataCommon:
    """A class implementing common plot data."""

    def __init__(self, channel: "DeviceChannel"):
        """Initialize common plot data for one channel."""
        self._xdata: list[Any] = []
        self._ydata: list[Any] = []
        self._vdim = channel.data.vdim
        self._chan = channel.data.chan
        for _ in range(self._vdim):
            self._xdata.append([])
            self._ydata.append([])
        self._samples_max = 0
        self._trigger_x: float | None = None

    @property
    def chan(self) -> int:
        """Return the channel id."""
        return self._chan

    @property
    def xdata(self) -> list[list[Any]]:
        """Return X-axis data."""
        return self._xdata

    @property
    def ydata(self) -> list[list[Any]]:
        """Return Y-axis data."""
        return self._ydata

    @property
    def samples_max(self) -> int:
        """Return the maximum retained sample count."""
        return self._samples_max

    @samples_max.setter
    def samples_max(self, smax: int) -> None:
        """Set the maximum retained sample count."""
        self._samples_max = smax

    @property
    def trigger_x(self) -> float | None:
        """Return last trigger marker X position."""
        return self._trigger_x

    def set_trigger_marker(self, xpos: float | None) -> None:
        """Store trigger marker X position."""
        self._trigger_x = xpos

    def xdata_extend(self, data: list[list[Any]]) -> None:
        """Append X-axis data."""
        for i, xdata in enumerate(self._xdata):
            xdata.extend(data[i])

    def ydata_extend(self, data: list[list[Any]]) -> None:
        """Append Y-axis data."""
        for i, ydata in enumerate(self._ydata):
            ydata.extend(data[i])

    def xdata_extend_max(self, data: list[list[Any]]) -> None:
        """Append X-axis data and clamp to the sample limit."""
        for i, _ in enumerate(self._xdata):
            self._xdata[i].extend(data[i])
            remove = len(self._xdata[i]) - self._samples_max
            if remove > 0:
                self._xdata[i] = self._xdata[i][remove:]

    def ydata_extend_max(self, data: list[list[Any]]) -> None:
        """Append Y-axis data and clamp to the sample limit."""
        for i, _ in enumerate(self._xdata):
            self._ydata[i].extend(data[i])
            remove = len(self._ydata[i]) - self._samples_max
            if remove > 0:
                self._ydata[i] = self._ydata[i][remove:]


class PlotDataAxesMpl(PlotDataCommon):
    """A class implementing common matplotlib axes logic."""

    def __init__(
        self,
        ax: "Axes",
        channel: "DeviceChannel",
        fmt: list[str] | None = None,
    ):
        """Initialize matplotlib-specific plot data."""
        super().__init__(channel)

        if not channel.data.is_numerical:
            raise TypeError

        self._ax = ax
        if not fmt:
            self._fmt = ["" for _ in range(channel.data.vdim)]
        else:
            assert (
                len(fmt) == channel.data.vdim
            ), "fmt must match vectors in configured channel"
            self._fmt = fmt

        self._lns: list["Line2D"] = []
        for i in range(channel.data.vdim):
            lines = self._ax.plot([], [], self._fmt[i])
            self._lns.append(lines[0])
        self._trigger_line = self._ax.axvline(
            0.0,
            color="tab:red",
            linestyle="--",
            linewidth=1.0,
            visible=False,
        )

        self.grid_set(True)
        if len(channel.data.name) > 0:  # pragma: no cover
            self.plot_title = channel.data.name

    def __str__(self) -> str:
        """Return a compact debug representation."""
        return "PlotDataAxesMpl" + "(channel=" + str(self.chan) + ")"

    @property
    def ax(self) -> "Axes":
        """Return the matplotlib axes."""
        return self._ax

    @property
    def lns(self) -> list["Line2D"]:
        """Return animated line objects."""
        return self._lns

    @property
    def trigger_line(self) -> "Line2D":
        """Return trigger marker line."""
        return self._trigger_line

    @property
    def xlim(self) -> Any:
        """Return current X limits."""
        assert self._ax
        return self._ax.get_xlim()

    @property
    def ylim(self) -> Any:
        """Return current Y limits."""
        assert self._ax
        return self._ax.get_ylim()

    @property
    def plot_title(self) -> Any:
        """Return the plot title."""
        assert self._ax
        return self._ax.get_title()

    @plot_title.setter
    def plot_title(self, title: str) -> None:
        """Set the plot title."""
        assert self._ax
        self._ax.set_title(title)

    def set_xlim(self, xlim: tuple[Any, Any]) -> None:
        """Set X-axis limits."""
        assert self._ax
        self._ax.set_xlim(*xlim)

    def set_ylim(self, ylim: tuple[Any, Any]) -> None:
        """Set Y-axis limits."""
        assert self._ax
        self._ax.set_ylim(*ylim)

    def plot(self) -> None:
        """Plot all stored series."""
        assert self._ax
        for i, data in enumerate(self._ydata):
            if self._xdata[i]:
                self._ax.plot(self._xdata[i], data, self._fmt[i])
            else:
                self._ax.plot(data, self._fmt[i])
        if self._trigger_x is not None:
            self._trigger_line.set_xdata([self._trigger_x, self._trigger_x])
            self._trigger_line.set_visible(True)

    def xaxis_disable(self) -> None:
        """Hide X-axis ticks."""
        self.xaxis_set_ticks([])

    def xaxis_set_ticks(self, ticks: list[Any]) -> None:
        """Set explicit X-axis ticks."""
        assert self._ax
        self._ax.get_xaxis().set_ticks(ticks)

    def grid_set(self, enable: bool) -> None:
        """Enable or disable the grid."""
        assert self._ax
        self._ax.grid(enable)
