"""Shared static-plot plugin base for dedicated plot-type plugins."""

from typing import TYPE_CHECKING, Any

from nxscli.logger import logger

from nxscli_mpl.plot_mpl import MplManager
from nxscli_mpl.plugins._static_common import _PluginStaticBase
from nxscli_mpl.plugins._typed_static_strategies import get_static_strategy

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
            MplManager.show_nonblocking()
        return self._plot

    def _render_pdata(self, pdata: Any) -> None:  # pragma: no cover
        series = [[float(v) for v in vec] for vec in pdata.ydata]
        strategy = get_static_strategy(self.plot_type)
        if strategy.render(
            pdata,
            series,
            samples=self._samples,
            hist_bins=self._hist_bins,
        ):
            return
        xvals, yvals = strategy.build_xy(
            series,
            samples=self._samples,
            hist_bins=self._hist_bins,
        )

        for i, line in enumerate(pdata.lns):
            if i < len(yvals):
                line.set_data(xvals[i], yvals[i])
            else:
                line.set_data([], [])
        pdata.ax.relim()
        pdata.ax.autoscale_view()
