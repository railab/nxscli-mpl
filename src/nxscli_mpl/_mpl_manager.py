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
    def show(block: bool = True) -> None:
        """Show an animation."""
        plt.show(block=block)  # pragma: no cover

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
