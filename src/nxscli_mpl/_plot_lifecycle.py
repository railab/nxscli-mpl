"""Private matplotlib plot lifecycle helpers."""

from typing import TYPE_CHECKING, Any

from nxscli.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def clear_animations(ani: list[Any]) -> list[Any]:
    """Stop registered animations and return an empty list."""
    for item in ani:
        try:
            item.stop()
        except Exception:
            pass
    return []


def clear_plot_data(axes: list["Axes"]) -> None:
    """Clear all subplot axes."""
    if len(axes) > 0:  # pragma: no cover
        for ax in axes:
            if ax is not None:
                ax.cla()


def close_surface(
    fig: "Figure | None",
    widget: Any,
    close_figure: "Callable[[Figure], None]",
) -> Any:
    """Close figure and attached widget, returning the cleared widget value."""
    if fig is not None:
        close_figure(fig)

    if widget is not None:
        close = getattr(widget, "close", None)
        if callable(close):
            close()
    return None


def is_qwidget(obj: Any) -> bool:
    """Return whether object is a Qt widget."""
    try:
        import PyQt6.QtWidgets as QtWidgets  # type: ignore[import-not-found]  # noqa: N813,E501
    except Exception:
        return False
    return isinstance(obj, QtWidgets.QWidget)


def attached_canvas_widget(
    fig: "Figure", widget_checker: "Callable[[Any], bool]"
) -> Any:
    """Return a QWidget-compatible matplotlib canvas for attached mode."""
    canvas = getattr(fig, "canvas", None)
    if widget_checker(canvas):
        return canvas

    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    except Exception:
        logger.warning("attached matplotlib mode requires Qt canvas backend")
        return None

    figure_canvas = FigureCanvasQTAgg
    return figure_canvas(fig)  # type: ignore[no-untyped-call]
