"""Private static render strategies for dedicated plot types."""

from typing import Any, Protocol

import numpy as np
from nxscli.transforms.operators_window import (
    fft_spectrum,
    histogram_counts,
    xy_relation,
)


class StaticRenderStrategy(Protocol):
    """Behavior contract for one static plot rendering mode."""

    def build_xy(  # pragma: no cover
        self,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """Build x/y values for line-based rendering."""
        raise NotImplementedError

    def render(  # pragma: no cover
        self,
        pdata: Any,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> bool:
        """Render directly and return whether default rendering is skipped."""
        raise NotImplementedError


class TimeseriesStaticStrategy:
    """Default line rendering for raw sample series."""

    def build_xy(  # pragma: no cover
        self,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """Build x/y pairs for raw timeseries lines."""
        del samples, hist_bins
        xvals = [[float(i) for i in range(len(vec))] for vec in series]
        return xvals, series

    def render(  # pragma: no cover
        self,
        pdata: Any,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> bool:
        """Leave rendering to the default line path."""
        del pdata, series, samples, hist_bins
        return False


class FftStaticStrategy:
    """Line rendering strategy for FFT plots."""

    def build_xy(  # pragma: no cover
        self,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """Build FFT frequency/amplitude series."""
        del samples, hist_bins
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

    def render(  # pragma: no cover
        self,
        pdata: Any,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> bool:
        """Leave rendering to the default line path."""
        del pdata, series, samples, hist_bins
        return False


class HistogramStaticStrategy:
    """Bar rendering strategy for histogram plots."""

    def build_xy(
        self,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """Build histogram edge/count series."""
        del samples
        bins = max(1, hist_bins)
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

    def render(
        self,
        pdata: Any,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> bool:
        """Render histogram bars directly on the axes."""
        del samples
        bins = max(1, hist_bins)
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
        return True


class XyStaticStrategy:
    """Scatter strategy for XY relation plots."""

    _fallback = TimeseriesStaticStrategy()

    def build_xy(
        self,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """Build XY relation coordinates for paired series."""
        del hist_bins
        if len(series) < 2:
            return self._fallback.build_xy(
                series, samples=samples, hist_bins=0
            )
        xvals: list[list[float]] = []
        yvals: list[list[float]] = []
        for i in range(1, len(series)):
            rel = xy_relation(series[0], series[i], window=samples or 65536)
            xvals.append([float(x) for x in rel.x.tolist()])
            yvals.append([float(y) for y in rel.y.tolist()])
        return xvals, yvals

    def render(
        self,
        pdata: Any,
        series: list[list[float]],
        *,
        samples: int,
        hist_bins: int,
    ) -> bool:
        """Leave rendering to the default line path."""
        del pdata, series, samples, hist_bins
        return False


_TIMESERIES = TimeseriesStaticStrategy()
_STRATEGIES: dict[str, StaticRenderStrategy] = {
    "timeseries": _TIMESERIES,
    "fft": FftStaticStrategy(),
    "histogram": HistogramStaticStrategy(),
    "xy": XyStaticStrategy(),
}


def get_static_strategy(plot_type: str) -> StaticRenderStrategy:
    """Return the dedicated strategy for a plot type."""
    return _STRATEGIES.get(plot_type, _TIMESERIES)
