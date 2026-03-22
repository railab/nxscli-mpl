"""Private matplotlib manager helpers."""

import time
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers
from matplotlib.animation import FuncAnimation
from nxscli.logger import logger

from nxscli_mpl._plot_constants import DEFAULT_DPI

if TYPE_CHECKING:
    from matplotlib.figure import Figure


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
        """Handle Matplotlib events."""
        manager = _pylab_helpers.Gcf.get_active()
        if manager is not None:
            canvas = manager.canvas
            if canvas.figure.stale:
                canvas.draw_idle()
            canvas.start_event_loop(interval)
        else:
            time.sleep(interval)

    @staticmethod
    def show() -> None:
        """Show a blocking matplotlib window."""
        MplManager._show_managers()
        plt.show(block=True)  # pragma: no cover

    @staticmethod
    def show_nonblocking() -> None:
        """Show a nonblocking matplotlib window and flush one GUI tick."""
        MplManager._show_managers()
        plt.show(block=False)  # pragma: no cover
        plt.pause(0.001)

    @staticmethod
    def _show_managers() -> None:
        """Ask existing figure managers to present their windows."""
        for manager in _pylab_helpers.Gcf.get_all_fig_managers():
            MplManager._present_manager(manager)

    @staticmethod
    def _present_manager(manager: Any) -> None:
        """Present one figure manager window."""
        try:
            manager.show()
        except Exception:
            pass
        window = getattr(manager, "window", None)
        if window is None:
            return
        try:
            window.show()
        except Exception:
            pass
        try:
            window.raise_()
        except Exception:
            pass
        try:
            window.activateWindow()
        except Exception:
            pass

    @staticmethod
    def style_set(style: list[str]) -> None:
        """Configure matplotlib."""
        logger.info("plt.style %s", str(style))
        plt.style.use(style)

    @staticmethod
    def figure(dpi: float = DEFAULT_DPI) -> "Figure":
        """Get figure."""
        return plt.figure(dpi=dpi)

    @staticmethod
    def func_animation(**kwargs: Any) -> Any:
        """Create animation."""
        return FuncAnimation(**kwargs)

    @staticmethod
    def close(fig: "Figure") -> None:
        """Close figure."""
        if plt.fignum_exists(fig.number):  # pragma: no cover
            plt.close(fig)
