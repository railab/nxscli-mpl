"""Dedicated polar plot plugin."""

from typing import Any

from nxscli.logger import logger
from nxscli.transforms.operators_window import polar_relation

from nxscli_mpl.plugins._typed_static import PluginTypedStatic


class PluginPolar(PluginTypedStatic):
    """Render static polar view from two channels."""

    plot_type = "polar"

    def __init__(self) -> None:
        """Initialize polar plugin."""
        super().__init__()
        self._polar_ax: Any = None
        self._single_channel_mode = False

    def start(self, kwargs: Any) -> bool:
        """Start and validate polar channel selection."""
        ok = super().start(kwargs)
        if not ok:
            return False
        first_vdim = len(self._plot.plist[0].ydata)
        self._single_channel_mode = first_vdim >= 2
        if not self._single_channel_mode and len(self._plot.plist) < 2:
            raise ValueError(
                "polar plot requires channel with >=2 vectors or two channels"
            )
        return True

    def _ensure_polar_axes(self, pdata: Any) -> Any:
        if self._polar_ax is not None:
            return self._polar_ax

        src_ax = pdata.ax
        spec = src_ax.get_subplotspec()
        src_ax.set_visible(False)
        self._polar_ax = self._plot.fig.add_subplot(spec, projection="polar")
        return self._polar_ax

    def _render_pdata(self, pdata: Any) -> None:
        """Render one polar chart from first two selected channels."""
        if pdata is not self._plot.plist[0]:
            try:
                pdata.ax.set_visible(False)
            except Exception:
                pass
            return

        first = self._plot.plist[0]
        if self._single_channel_mode:
            theta_src = [[float(v) for v in first.ydata[0]]]
            radius_src = [[float(v) for v in first.ydata[1]]]
            nvec = min(len(theta_src), len(radius_src), len(pdata.lns))
        else:
            second = self._plot.plist[1]
            xsrc = [[float(v) for v in vec] for vec in first.ydata]
            ysrc = [[float(v) for v in vec] for vec in second.ydata]
            nvec = min(len(xsrc), len(ysrc), len(pdata.lns))

        ax = self._ensure_polar_axes(pdata)
        ax.clear()

        for i in range(nvec):
            if self._single_channel_mode:
                theta = theta_src[i]
                radius = radius_src[i]
            else:
                rel = polar_relation(
                    xsrc[i],
                    ysrc[i],
                    window=max(len(xsrc[i]), len(ysrc[i]), 2),
                )
                theta = rel.theta.tolist()
                radius = rel.radius.tolist()
            src_line = pdata.lns[i]
            ax.plot(
                theta,
                radius,
                color=src_line.get_color(),
                linestyle=src_line.get_linestyle(),
                marker=src_line.get_marker(),
            )

        ax.set_title("Polar Plot")
        logger.info(
            "polar rendered using channels %d/%d",
            self._plot.plist[0].chan,
            (
                self._plot.plist[0].chan
                if self._single_channel_mode
                else self._plot.plist[1].chan
            ),
        )
