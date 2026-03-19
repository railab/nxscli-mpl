"""Shared static-plot plugin base for dedicated plot-type plugins."""

from typing import TYPE_CHECKING, Any

import numpy as np
from nxscli.logger import logger
from nxscli.transforms.operators_window import (
    fft_spectrum,
    histogram_counts,
    xy_relation,
)

from nxscli_mpl.plot_mpl import MplManager
from nxscli_mpl.plugins._static_common import _PluginStaticBase

if TYPE_CHECKING:
    from nxscli_mpl.plot_mpl import PluginPlotMpl


class PluginTypedStatic(_PluginStaticBase):
    """Static plot plugin for one explicit rendering type."""

    plot_type = "timeseries"

    def __init__(self) -> None:
        """Initialize typed static plugin."""
        super().__init__()
        self._hist_bins: int = 32

    def _final(self) -> None:
        logger.info("plot %s DONE", self.plot_type)

    def wait_for_plugin(self) -> bool:  # pragma: no cover
        """Wait for figure to close."""
        done = True
        if MplManager.fig_is_open():
            done = False
            MplManager.pause(1)
        return done

    def start(self, kwargs: Any) -> bool:  # pragma: no cover
        """Start typed static plugin."""
        logger.info("start %s %s", self.plot_type, str(kwargs))
        self._hist_bins = int(kwargs.get("bins", 32))
        if not self._start_plot(kwargs):
            return False

        if self._samples and self.plot_type in ("timeseries", "xy"):
            self._set_initial_xlim()

        self.thread_start(self._plot)
        return True

    def result(self) -> "PluginPlotMpl":  # pragma: no cover
        """Render and return plot."""
        assert self._plot

        for pdata in self._plot.plist:
            self._render_pdata(pdata)

        self._save_plot()

        if self._plot.mode == "detached":
            MplManager.show(block=False)
        return self._plot

    def _render_pdata(self, pdata: Any) -> None:  # pragma: no cover
        series = [[float(v) for v in vec] for vec in pdata.ydata]
        if self.plot_type == "histogram":
            self._render_hist_bars(pdata, series)
            return
        xvals, yvals = self._build_xy(series)

        for i, line in enumerate(pdata.lns):
            if i < len(yvals):
                line.set_data(xvals[i], yvals[i])
            else:
                line.set_data([], [])
        pdata.ax.relim()
        pdata.ax.autoscale_view()

    def _render_hist_bars(  # pragma: no cover
        self, pdata: Any, series: list[list[float]]
    ) -> None:
        bins = max(1, self._hist_bins)
        pdata.ax.cla()
        for i, vec in enumerate(series):
            res = histogram_counts(vec, bins=bins, range_mode="auto")
            if int(res.counts.size) == 0 or int(res.edges.size) < 2:
                continue
            centers = res.edges[:-1]
            widths = np.diff(res.edges)
            alpha = 0.6 if i == 0 else 0.35
            pdata.ax.bar(centers, res.counts, width=widths, alpha=alpha)
        pdata.ax.set_title("Histogram")
        pdata.ax.relim()
        pdata.ax.autoscale_view()

    def _build_xy(  # pragma: no cover
        self, series: list[list[float]]
    ) -> tuple[list[list[float]], list[list[float]]]:
        if self.plot_type == "fft":
            return self._build_fft(series)
        if self.plot_type == "histogram":
            return self._build_hist(series)
        if self.plot_type == "xy":
            return self._build_scatter(series)
        return self._build_timeseries(series)

    def _build_timeseries(  # pragma: no cover
        self, series: list[list[float]]
    ) -> tuple[list[list[float]], list[list[float]]]:
        xvals = [[float(i) for i in range(len(vec))] for vec in series]
        return xvals, series

    def _build_fft(  # pragma: no cover
        self, series: list[list[float]]
    ) -> tuple[list[list[float]], list[list[float]]]:
        xvals: list[list[float]] = []
        yvals: list[list[float]] = []
        for vec in series:
            res = fft_spectrum(vec, window_fn="hann")
            if int(res.freq.size) == 0:
                xvals.append([])
                yvals.append([])
                continue
            xvals.append([float(x) for x in res.freq.tolist()])
            yvals.append([float(y) for y in res.amplitude.tolist()])
        return xvals, yvals

    def _build_hist(  # pragma: no cover
        self, series: list[list[float]]
    ) -> tuple[list[list[float]], list[list[float]]]:
        bins = max(1, self._hist_bins)
        xvals: list[list[float]] = []
        yvals: list[list[float]] = []
        for vec in series:
            res = histogram_counts(vec, bins=bins, range_mode="auto")
            if int(res.counts.size) == 0 or int(res.edges.size) < 2:
                xvals.append([])
                yvals.append([])
                continue
            xvals.append([float(x) for x in res.edges[:-1].tolist()])
            yvals.append([float(y) for y in res.counts.tolist()])
        return xvals, yvals

    def _build_scatter(  # pragma: no cover
        self, series: list[list[float]]
    ) -> tuple[list[list[float]], list[list[float]]]:
        if len(series) < 2:
            return self._build_timeseries(series)
        xvals: list[list[float]] = []
        yvals: list[list[float]] = []
        for i in range(1, len(series)):
            rel = xy_relation(
                series[0], series[i], window=self._samples or 65536
            )
            xvals.append([float(x) for x in rel.x.tolist()])
            yvals.append([float(y) for y in rel.y.tolist()])
        return xvals, yvals
