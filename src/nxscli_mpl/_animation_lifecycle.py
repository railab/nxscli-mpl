"""Private matplotlib animation lifecycle helpers."""

from typing import TYPE_CHECKING, Any

from matplotlib.animation import FFMpegWriter, PillowWriter
from nxscli.logger import logger

from nxscli_mpl._mpl_manager import MplManager

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D


def setup_writer(
    fig: "Figure",
    write: str,
) -> PillowWriter | FFMpegWriter | None:
    """Create and initialize an animation writer when requested."""
    if not write:
        return None

    fps = 10
    logger.info("writer animation to file=%s, fps=%d", write, fps)
    tmp = write.split(".")
    if tmp[-1] == "gif":
        writer: PillowWriter | FFMpegWriter = PillowWriter(fps=fps)
    elif tmp[-1] == "mp4":
        writer = FFMpegWriter(fps=fps, bitrate=200)
    else:
        raise TypeError

    writer.setup(fig, write)
    return writer


def stop_animation(
    ani: Any,
    writer: PillowWriter | FFMpegWriter | None,
) -> None:
    """Stop a matplotlib animation and finish the writer if present."""
    if ani and ani.event_source:
        ani.pause()
    if writer:
        writer.finish()


def update_animation_common(
    frame: tuple[list[Any], list[Any], float | None],
    default_lines: list["Line2D"],
    updater: (
        "Callable["
        "[tuple[list[Any], list[Any], float | None]], list[Line2D] | None"
        "]"
    ),
    writer: PillowWriter | FFMpegWriter | None,
) -> list["Line2D"]:
    """Handle empty-frame skipping and optional writer capture."""
    if len(frame[0]) == 0 or len(frame[1]) == 0:
        return default_lines

    lines = updater(frame)
    assert lines
    if writer:
        writer.grab_frame()
    return lines


def start_animation(
    *,
    fig: "Figure",
    update: "Callable[[Any], list[Line2D]]",
    frames: "Callable[[], Generator[Any, None, None]]",
    init: "Callable[[], list[Line2D]]",
) -> Any:
    """Create the matplotlib animation through the backend manager."""
    return MplManager.func_animation(
        fig=fig,
        func=update,
        frames=frames,
        init_func=init,
        interval=1,
        blit=False,
        cache_frame_data=False,
    )
