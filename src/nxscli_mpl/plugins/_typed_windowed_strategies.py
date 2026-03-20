"""Private windowed transform strategies for FFT and histogram plots."""

from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np
from nxscli.transforms.models import FftResult, HistogramResult
from nxscli.transforms.operators_window import fft_spectrum, histogram_counts

from nxscli_mpl._plot_constants import (
    AXIS_DECAY_FACTOR,
    AXIS_MIN_MAGNITUDE,
    AXIS_PADDING_FACTOR,
)


class _LineLike(Protocol):
    """Minimal line surface used by windowed strategies."""

    def set_data(self, x: object, y: object) -> None:
        """Assign line data."""
        raise NotImplementedError


class _AxesLike(Protocol):
    """Minimal axes surface used by windowed strategies."""

    def set_xlim(self, low: float, high: float) -> None:
        """Set x limits."""
        raise NotImplementedError

    def set_ylim(self, low: float, high: float) -> None:
        """Set y limits."""
        raise NotImplementedError

    def cla(self) -> None:
        """Clear axes."""
        raise NotImplementedError

    def bar(
        self,
        x: object,
        height: object,
        *,
        width: object,
        alpha: float,
    ) -> None:
        """Draw bars."""
        raise NotImplementedError

    def set_title(self, title: str) -> None:
        """Set title."""
        raise NotImplementedError


class _WindowedPlotDataLike(Protocol):
    """Minimal plot-data surface used by windowed strategies."""

    @property
    def ax(self) -> _AxesLike:
        """Return axes."""
        raise NotImplementedError

    @property
    def lns(self) -> Sequence[_LineLike]:
        """Return line artists."""
        raise NotImplementedError


@dataclass
class WindowedTransformState:
    """Mutable state shared across windowed transform updates."""

    fft_xmax: float | None = None
    ymax_locked: float | None = None
    hist_range: tuple[float, float] | None = None


class WindowedTransformStrategy(Protocol):
    """Behavior contract for one windowed transform type."""

    def processor(
        self,
        window: np.ndarray,
        *,
        bins: int,
        window_fn: str,
        range_mode: str,
        state: WindowedTransformState,
    ) -> object:
        """Transform one window of samples."""
        raise NotImplementedError

    def update_plot(
        self,
        pdata: _WindowedPlotDataLike,
        outputs: dict[str, object],
        *,
        proc_names: list[str],
        state: WindowedTransformState,
    ) -> None:
        """Apply transform outputs to the plot state."""
        raise NotImplementedError


def _lock_axis(  # pragma: no cover
    pdata: _WindowedPlotDataLike,
    state: WindowedTransformState,
    *,
    xmax: float | None,
    ymax: float,
) -> None:
    ymax_safe = max(AXIS_MIN_MAGNITUDE, float(ymax))
    if state.ymax_locked is None:
        state.ymax_locked = ymax_safe
    else:
        prev = state.ymax_locked
        if ymax_safe > prev:
            state.ymax_locked = 0.85 * prev + 0.15 * ymax_safe
        else:
            state.ymax_locked = max(ymax_safe, prev * AXIS_DECAY_FACTOR)

    if xmax is not None:
        pdata.ax.set_xlim(0.0, float(xmax))
    pdata.ax.set_ylim(0.0, float(state.ymax_locked) * AXIS_PADDING_FACTOR)


class FftWindowedStrategy:
    """FFT-specific windowed transform behavior."""

    def processor(
        self,
        window: np.ndarray,
        *,
        bins: int,
        window_fn: str,
        range_mode: str,
        state: WindowedTransformState,
    ) -> object:
        """Compute FFT output for a single window."""
        del bins, range_mode, state
        return fft_spectrum(window, window_fn=window_fn)

    def update_plot(  # pragma: no cover
        self,
        pdata: _WindowedPlotDataLike,
        outputs: dict[str, object],
        *,
        proc_names: list[str],
        state: WindowedTransformState,
    ) -> None:
        """Apply FFT transform outputs to lines and axes."""
        ymax = 0.0
        for i, line in enumerate(pdata.lns):
            raw = outputs.get(proc_names[i])
            if raw is None or not isinstance(raw, FftResult):
                continue
            line.set_data(raw.freq.tolist(), raw.amplitude.tolist())
            if int(raw.freq.size) > 0:
                state.fft_xmax = float(raw.freq[-1])
            if int(raw.amplitude.size) > 0:
                ymax = max(ymax, float(np.max(raw.amplitude)))
        _lock_axis(pdata, state, xmax=state.fft_xmax, ymax=ymax)


class HistogramWindowedStrategy:
    """Histogram-specific windowed transform behavior."""

    def processor(
        self,
        window: np.ndarray,
        *,
        bins: int,
        window_fn: str,
        range_mode: str,
        state: WindowedTransformState,
    ) -> object:
        """Compute histogram output for a single window."""
        del window_fn
        mode, value_range = self._hist_mode(range_mode, state.hist_range)
        return histogram_counts(
            window,
            bins=bins,
            range_mode=mode,
            value_range=value_range,
        )

    def update_plot(  # pragma: no cover
        self,
        pdata: _WindowedPlotDataLike,
        outputs: dict[str, object],
        *,
        proc_names: list[str],
        state: WindowedTransformState,
    ) -> None:
        """Redraw histogram bars and update axis locks."""
        updates: list[tuple[np.ndarray, np.ndarray]] = []
        for name in proc_names:
            raw = outputs.get(name)
            if raw is None or not isinstance(raw, HistogramResult):
                continue
            updates.append((raw.counts, raw.edges))

        if not updates:
            return

        if state.hist_range is None:
            first_edges = updates[0][1]
            if int(first_edges.size) >= 2:
                state.hist_range = (
                    float(first_edges[0]),
                    float(first_edges[-1]),
                )

        ymax = 0.0
        pdata.ax.cla()
        for i, (counts, edges) in enumerate(updates):
            if int(edges.size) < 2:
                continue
            centers = edges[:-1]
            widths = np.diff(edges)
            alpha = 0.6 if i == 0 else 0.35
            pdata.ax.bar(centers, counts, width=widths, alpha=alpha)
            if int(counts.size) > 0:
                ymax = max(ymax, float(np.max(counts)))

        pdata.ax.set_title("Histogram Stream")
        if state.hist_range is not None:
            pdata.ax.set_xlim(state.hist_range[0], state.hist_range[1])
        _lock_axis(pdata, state, xmax=None, ymax=ymax)

    def _hist_mode(  # pragma: no cover
        self,
        range_mode: str,
        hist_range: tuple[float, float] | None,
    ) -> tuple[str, tuple[float, float] | None]:
        """Resolve histogram mode and optional fixed range."""
        if range_mode == "fixed":
            return "fixed", hist_range
        if hist_range is None:
            return "auto", None
        return "fixed", hist_range


_FFT = FftWindowedStrategy()
_STRATEGIES: dict[str, WindowedTransformStrategy] = {
    "fft": _FFT,
    "histogram": HistogramWindowedStrategy(),
}


def get_windowed_transform_strategy(
    plot_type: str,
) -> WindowedTransformStrategy:
    """Return the dedicated strategy for a plot type."""
    return _STRATEGIES.get(plot_type, _FFT)
