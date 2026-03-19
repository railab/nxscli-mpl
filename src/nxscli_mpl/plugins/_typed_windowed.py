"""Shared windowed dynamic plugins for typed plots."""

from typing import TYPE_CHECKING, Any, cast

import numpy as np
from matplotlib.animation import FuncAnimation
from nxscli.logger import logger
from nxscli.transforms.models import (
    FftResult,
    HistogramResult,
    PolarResult,
    XyResult,
)
from nxscli.transforms.operators_window import (
    fft_spectrum,
    histogram_counts,
    polar_relation,
    xy_relation,
)
from nxscli.transforms.pipeline import (
    TransformPipeline,
    WindowBinaryProcessor,
    WindowUnaryProcessor,
)

from nxscli_mpl.animation_mpl import _create_matplotlib_inputhook
from nxscli_mpl.plot_mpl import PluginAnimationCommonMpl
from nxscli_mpl.plugins._windowed_common import (
    _PluginAnimationListWindowedBase,
    _PluginFuncAnimationWindowedBase,
    _read_channel_pair,
    _read_channel_values,
    _SingleChannelAccumulator,
)

if TYPE_CHECKING:
    from nxscli.idata import PluginQueueData

    from nxscli_mpl.plot_mpl import PlotDataAxesMpl


class _WindowedTypedAnimation(PluginAnimationCommonMpl):
    """Windowed transform animation for FFT/histogram."""

    def __init__(
        self,
        fig: Any,
        pdata: "PlotDataAxesMpl",
        qdata: "PluginQueueData",
        write: str,
        *,
        plot_type: str,
        window: int,
        hop: int,
        bins: int,
        window_fn: str,
        range_mode: str,
    ) -> None:
        super().__init__(fig, pdata, qdata, write)
        self._plot_type = plot_type
        self._window = max(2, int(window))
        self._hop = int(hop)
        self._bins = max(1, int(bins))
        self._window_fn = str(window_fn)
        self._range_mode = str(range_mode)
        self._pipeline = TransformPipeline(max_points=self._window)
        self._proc_names: list[str] = []
        for i, _ in enumerate(pdata.lns):
            name = f"curve{i}"
            self._proc_names.append(name)
            self._pipeline.register(
                WindowUnaryProcessor(
                    name=name,
                    channel=name,
                    window=self._window,
                    hop=self._hop,
                    fn=self._processor_fn,
                )
            )
        self._fft_xmax: float | None = None
        self._ymax_locked: float | None = None
        self._hist_range: tuple[float, float] | None = None
        pdata.samples_max = self._window

    def start(self) -> None:  # pragma: no cover
        """Start animation with blit disabled for transformed axes redraw."""
        ani = FuncAnimation(
            fig=self._fig,
            func=lambda frame: self._animation_update_cmn(frame, self._pdata),
            frames=lambda: self._animation_frames(self._qdata),
            init_func=lambda: self._animation_init(self._pdata),
            interval=30,
            blit=False,
            cache_frame_data=False,
        )
        cast("Any", ani)._draw_was_started = True
        self._ani = cast("Any", ani)
        # tests may stop plugin before first draw; avoid matplotlib destructor
        # warning that pytest treats as failure.

    def _animation_update(  # pragma: no cover
        self, frame: tuple[list[Any], list[Any]], pdata: "PlotDataAxesMpl"
    ) -> list[Any]:
        pdata.xdata_extend_max(frame[0])
        pdata.ydata_extend_max(frame[1])
        batch = {
            name: [float(x) for x in vec]
            for name, vec in zip(self._proc_names, frame[1])
        }
        outputs = self._pipeline.ingest(batch)

        if self._plot_type == "fft":
            self._update_fft(pdata, outputs)
        else:
            self._update_hist(pdata, outputs)

        return pdata.lns

    def _processor_fn(self, window: np.ndarray) -> object:  # pragma: no cover
        if self._plot_type == "fft":
            return fft_spectrum(window, window_fn=self._window_fn)

        mode, value_range = self._hist_mode()

        return histogram_counts(
            window,
            bins=self._bins,
            range_mode=mode,
            value_range=value_range,
        )

    def _hist_mode(  # pragma: no cover
        self,
    ) -> tuple[str, tuple[float, float] | None]:
        if self._range_mode == "fixed":
            return "fixed", self._hist_range
        if self._hist_range is None:
            return "auto", None
        return "fixed", self._hist_range

    def _lock_axis(  # pragma: no cover
        self, pdata: "PlotDataAxesMpl", xmax: float | None, ymax: float
    ) -> None:
        ymax_safe = max(1e-9, float(ymax))
        if self._ymax_locked is None:
            self._ymax_locked = ymax_safe
        else:
            prev = self._ymax_locked
            if ymax_safe > prev:
                self._ymax_locked = 0.85 * prev + 0.15 * ymax_safe
            else:
                self._ymax_locked = max(ymax_safe, prev * 0.995)

        if xmax is not None:
            pdata.ax.set_xlim(0.0, float(xmax))
        pdata.ax.set_ylim(0.0, float(self._ymax_locked) * 1.08)

    def _update_fft(  # pragma: no cover
        self, pdata: "PlotDataAxesMpl", outputs: dict[str, object]
    ) -> None:
        ymax = 0.0
        for i, line in enumerate(pdata.lns):
            raw = outputs.get(self._proc_names[i])
            if raw is None:
                continue
            if not isinstance(raw, FftResult):
                continue
            res = raw
            line.set_data(res.freq.tolist(), res.amplitude.tolist())
            if int(res.freq.size) > 0:
                self._fft_xmax = float(res.freq[-1])
            if int(res.amplitude.size) > 0:
                ymax = max(ymax, float(np.max(res.amplitude)))
        self._lock_axis(pdata, self._fft_xmax, ymax)

    def _update_hist(  # pragma: no cover
        self, pdata: "PlotDataAxesMpl", outputs: dict[str, object]
    ) -> None:
        updates: list[tuple[np.ndarray, np.ndarray]] = []
        for name in self._proc_names:
            raw = outputs.get(name)
            if raw is None:
                continue
            if not isinstance(raw, HistogramResult):
                continue
            res = raw
            updates.append((res.counts, res.edges))

        if not updates:
            return

        if self._hist_range is None and len(updates) > 0:
            first_edges = updates[0][1]
            if int(first_edges.size) >= 2:
                self._hist_range = (
                    float(first_edges[0]),
                    float(first_edges[-1]),
                )

        ymax = self._draw_histogram(pdata, updates)
        pdata.ax.set_title("Histogram Stream")
        if self._hist_range is not None:
            pdata.ax.set_xlim(self._hist_range[0], self._hist_range[1])
        self._lock_axis(pdata, None, ymax)

    def _draw_histogram(  # pragma: no cover
        self,
        pdata: "PlotDataAxesMpl",
        updates: list[tuple[np.ndarray, np.ndarray]],
    ) -> float:
        pdata.ax.cla()
        ymax = 0.0
        for i, (counts, edges) in enumerate(updates):
            if int(edges.size) < 2:
                continue
            centers = edges[:-1]
            widths = np.diff(edges)
            alpha = 0.6 if i == 0 else 0.35
            pdata.ax.bar(centers, counts, width=widths, alpha=alpha)
            if int(counts.size) > 0:
                ymax = max(ymax, float(np.max(counts)))
        return ymax


class _PluginTypedWindowed(_PluginAnimationListWindowedBase):
    """Windowed dynamic plugin for one typed transform."""

    plot_type = "fft"

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def get_inputhook(cls) -> Any:
        return _create_matplotlib_inputhook()

    def start(self, kwargs: Any) -> bool:  # pragma: no cover
        logger.info("start %s stream %s", self.plot_type, str(kwargs))

        self._build_plot(kwargs)
        self.clear()

        for i, pdata in enumerate(self._plot.plist):
            ani = _WindowedTypedAnimation(
                self._plot.fig,
                pdata,
                self._plot.qdlist[i],
                kwargs["write"],
                plot_type=self.plot_type,
                window=int(kwargs["window"]),
                hop=int(kwargs.get("hop", 0)),
                bins=int(kwargs.get("bins", 32)),
                window_fn=str(kwargs.get("window_fn", "hann")),
                range_mode=str(kwargs.get("range_mode", "auto")),
            )
            self._plot.ani_append(ani)
            ani.start()

        return True


class _PluginXyWindowed(_PluginFuncAnimationWindowedBase):
    """Windowed XY scatter animation using two channels."""

    def __init__(self) -> None:
        super().__init__()
        self._window = 256
        self._hop = 64
        self._align_policy = "truncate"
        self._pipeline: TransformPipeline
        self._xy_name = "xy"
        self._single_channel_mode = False
        self._single = _SingleChannelAccumulator(window=256, hop=64)

    @classmethod
    def get_inputhook(cls) -> Any:
        return _create_matplotlib_inputhook()

    def start(self, kwargs: Any) -> bool:  # pragma: no cover
        assert self._phandler
        chanlist = self._phandler.chanlist_plugin(kwargs["channels"])
        if len(chanlist) < 1:
            raise ValueError("xy_stream requires at least one channel")
        self._build_plot(kwargs)
        self._window = max(2, int(kwargs["window"]))
        self._hop = max(1, int(kwargs.get("hop", 0) or (self._window // 4)))
        self._align_policy = str(kwargs.get("align_policy", "truncate"))
        first_vdim = self._plot.qdlist[0].vdim
        self._single_channel_mode = first_vdim >= 2
        if not self._single_channel_mode and len(self._plot.qdlist) < 2:
            raise ValueError(
                "xy_stream requires channel with >=2 vectors or two channels"
            )
        self._pipeline = TransformPipeline(max_points=self._window)
        self._pipeline.register(
            WindowBinaryProcessor(
                name=self._xy_name,
                left_channel="x",
                right_channel="y",
                window=self._window,
                hop=self._hop,
                fn=lambda x, y: xy_relation(
                    x.tolist(),
                    y.tolist(),
                    window=self._window,
                    align_policy=self._align_policy,
                ),
            )
        )
        self._xlim: tuple[float, float] | None = None
        self._ylim: tuple[float, float] | None = None
        self._single = _SingleChannelAccumulator(
            window=self._window, hop=self._hop
        )

        for idx, pdata in enumerate(self._plot.plist):
            if idx != 0:
                pdata.ax.set_visible(False)

        self._ani = FuncAnimation(
            fig=self._plot.fig,
            func=lambda *_: self._update_xy(),
            interval=30,
            blit=False,
            cache_frame_data=False,
        )
        cast("Any", self._ani)._draw_was_started = True
        return True

    def _collect_xy(self) -> XyResult | None:  # pragma: no cover
        if self._single_channel_mode:
            xs, ys = _read_channel_pair(self._plot.qdlist[0])
            collected = self._single.collect(xs, ys)
            if collected is None:
                return None
            left, right = collected
            return xy_relation(
                left,
                right,
                window=self._window,
                align_policy=self._align_policy,
            )

        qx = self._plot.qdlist[0]
        qy = self._plot.qdlist[1]
        xs = _read_channel_values(qx)
        ys = _read_channel_values(qy)
        count = min(len(xs), len(ys))
        outputs = self._pipeline.ingest({"x": xs[:count], "y": ys[:count]})
        raw = outputs.get(self._xy_name)
        if raw is None or not isinstance(raw, XyResult):
            return None
        return raw

    def _update_xy(self) -> list[Any]:  # pragma: no cover
        rel = self._collect_xy()
        if rel is None:
            return []

        pdata = self._plot.plist[0]
        if len(pdata.lns) == 0:
            return []
        pdata.lns[0].set_data(rel.x.tolist(), rel.y.tolist())
        pdata.lns[0].set_visible(True)
        for i in range(1, len(pdata.lns)):
            pdata.lns[i].set_visible(False)
        pdata.ax.set_title("XY Stream")
        if int(rel.x.size) > 0 and int(rel.y.size) > 0:
            xmin = float(np.min(rel.x))
            xmax = float(np.max(rel.x))
            ymin = float(np.min(rel.y))
            ymax = float(np.max(rel.y))
            padx = max(1e-9, (xmax - xmin) * 0.1)
            pady = max(1e-9, (ymax - ymin) * 0.1)
            cur_xlim = (xmin - padx, xmax + padx)
            cur_ylim = (ymin - pady, ymax + pady)
            if self._xlim is None:
                self._xlim = cur_xlim
                self._ylim = cur_ylim
            else:
                assert self._ylim is not None
                self._xlim = (
                    min(self._xlim[0], cur_xlim[0]),
                    max(self._xlim[1], cur_xlim[1]),
                )
                self._ylim = (
                    min(self._ylim[0], cur_ylim[0]),
                    max(self._ylim[1], cur_ylim[1]),
                )
            pdata.ax.set_xlim(*self._xlim)
            pdata.ax.set_ylim(*self._ylim)
        return pdata.lns


class PluginFftStream(_PluginTypedWindowed):
    """FFT stream plot."""

    plot_type = "fft"


class PluginHistStream(_PluginTypedWindowed):
    """Histogram stream plot."""

    plot_type = "histogram"


class PluginXyStream(_PluginXyWindowed):
    """XY stream plot."""


class _PluginPolarWindowed(_PluginFuncAnimationWindowedBase):
    """Windowed polar animation using two channels."""

    def __init__(self) -> None:
        super().__init__()
        self._window = 256
        self._hop = 64
        self._align_policy = "truncate"
        self._pipeline: TransformPipeline
        self._polar_name = "polar"
        self._polar_ax: Any = None
        self._polar_lines: list[Any] = []
        self._rmax: float | None = None
        self._single_channel_mode = False
        self._single = _SingleChannelAccumulator(window=256, hop=64)

    @classmethod
    def get_inputhook(cls) -> Any:
        return _create_matplotlib_inputhook()

    def _configure_polar_axes(self) -> None:  # pragma: no cover
        pdata = self._plot.plist[0]
        src_ax = pdata.ax
        spec = src_ax.get_subplotspec()
        src_ax.set_visible(False)
        if spec is None:
            self._polar_ax = self._plot.fig.add_subplot(
                1, 1, 1, projection="polar"
            )
        else:
            self._polar_ax = self._plot.fig.add_subplot(
                spec, projection="polar"
            )
        self._polar_lines = []
        if self._single_channel_mode:
            count = min(1, len(pdata.lns))
        else:
            count = min(len(pdata.lns), len(self._plot.plist[1].lns))
        for i in range(count):
            src_line = pdata.lns[i]
            lines = self._polar_ax.plot(
                [],
                [],
                color=src_line.get_color(),
                linestyle=src_line.get_linestyle(),
                marker=src_line.get_marker(),
            )
            self._polar_lines.append(lines[0])
        self._polar_ax.set_title("Polar Stream")

    def start(self, kwargs: Any) -> bool:  # pragma: no cover
        assert self._phandler
        chanlist = self._phandler.chanlist_plugin(kwargs["channels"])
        if len(chanlist) < 1:
            raise ValueError("polar_stream requires at least one channel")
        self._build_plot(kwargs)
        self._window = max(2, int(kwargs["window"]))
        self._hop = max(1, int(kwargs.get("hop", 0) or (self._window // 4)))
        self._align_policy = str(kwargs.get("align_policy", "truncate"))
        first_vdim = self._plot.qdlist[0].vdim
        self._single_channel_mode = first_vdim >= 2
        if not self._single_channel_mode and len(self._plot.qdlist) < 2:
            raise ValueError(
                "polar_stream requires channel with >=2 vectors "
                "or two channels"
            )
        self._pipeline = TransformPipeline(max_points=self._window)
        self._pipeline.register(
            WindowBinaryProcessor(
                name=self._polar_name,
                left_channel="x",
                right_channel="y",
                window=self._window,
                hop=self._hop,
                fn=lambda x, y: polar_relation(
                    x.tolist(),
                    y.tolist(),
                    window=self._window,
                    align_policy=self._align_policy,
                ),
            )
        )
        self._rmax = None
        self._single = _SingleChannelAccumulator(
            window=self._window, hop=self._hop
        )

        for idx, pdata in enumerate(self._plot.plist):
            if idx != 0:
                pdata.ax.set_visible(False)
        self._configure_polar_axes()

        self._ani = FuncAnimation(
            fig=self._plot.fig,
            func=lambda *_: self._update_polar(),
            interval=30,
            blit=False,
            cache_frame_data=False,
        )
        cast("Any", self._ani)._draw_was_started = True
        return True

    def _update_polar(self) -> list[Any]:  # pragma: no cover
        values = self._collect_theta_radius()
        if values is None:
            return []
        theta, radius = values

        if self._polar_ax is None or len(self._polar_lines) == 0:
            return []
        self._polar_lines[0].set_data(theta.tolist(), radius.tolist())
        for i in range(1, len(self._polar_lines)):
            self._polar_lines[i].set_data([], [])

        if int(radius.size) > 0:
            cur = float(np.max(radius))
            if self._rmax is None:
                self._rmax = cur
            else:
                self._rmax = max(cur, self._rmax * 0.995)
            self._polar_ax.set_ylim(0.0, max(1e-9, self._rmax) * 1.08)

        return self._polar_lines

    def _collect_theta_radius(  # pragma: no cover
        self,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        if self._single_channel_mode:
            return self._collect_theta_radius_single()
        return self._collect_theta_radius_xy()

    def _collect_theta_radius_single(  # pragma: no cover
        self,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        xs, ys = _read_channel_pair(self._plot.qdlist[0])
        collected = self._single.collect(xs, ys)
        if collected is None:
            return None
        left, right = collected
        return (
            np.asarray(left, dtype=np.float64),
            np.asarray(right, dtype=np.float64),
        )

    def _collect_theta_radius_xy(  # pragma: no cover
        self,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        xs = _read_channel_values(self._plot.qdlist[0])
        ys = _read_channel_values(self._plot.qdlist[1])
        count = min(len(xs), len(ys))
        outputs = self._pipeline.ingest({"x": xs[:count], "y": ys[:count]})
        raw = outputs.get(self._polar_name)
        if raw is None or not isinstance(raw, PolarResult):
            return None
        return raw.theta, raw.radius


class PluginPolarStream(_PluginPolarWindowed):
    """Polar stream plot."""
