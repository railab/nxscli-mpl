"""Private matplotlib animation queue helpers."""

from typing import TYPE_CHECKING, Any

import numpy as np
from nxslib.nxscope import DNxscopeStreamBlock

from nxscli_mpl._plot_constants import ANIMATION_FRAME_DRAIN_LIMIT

if TYPE_CHECKING:
    from nxscli.idata import PluginQueueData


def fetch_animation_frame(
    qdata: "PluginQueueData",
    *,
    count: int,
    limit: int = ANIMATION_FRAME_DRAIN_LIMIT,
) -> tuple[list[np.ndarray[Any, Any]], list[np.ndarray[Any, Any]], int]:
    """Drain one animation frame from the queue and return updated counters."""
    x_chunks: list[np.ndarray[Any, Any]] = []
    y_chunks: list[list[np.ndarray[Any, Any]]] = [
        [] for _ in range(qdata.vdim)
    ]
    next_count = count

    for _ in range(limit):
        data = qdata.queue_get(block=False)
        if not data:
            break
        if not isinstance(data, list):
            raise RuntimeError("plot animation queue payload must be list")

        for block in data:
            if not isinstance(block, DNxscopeStreamBlock):
                raise RuntimeError(
                    "plot animation requires DNxscopeStreamBlock payload"
                )
            block_data = block.data
            assert isinstance(block_data, np.ndarray)
            nsamples = int(block_data.shape[0])
            if nsamples == 0:
                continue
            xr = np.arange(next_count, next_count + nsamples)
            x_chunks.append(xr)
            for i in range(qdata.vdim):
                y_chunks[i].append(block_data[:, i])
            next_count += nsamples

    xcat = (
        np.concatenate(x_chunks)
        if x_chunks
        else np.empty((0,), dtype=np.int64)
    )
    xdata = [xcat for _ in range(qdata.vdim)]
    ydata = [
        (
            np.concatenate(chunks)
            if chunks
            else np.empty((0,), dtype=np.float64)
        )
        for chunks in y_chunks
    ]
    return xdata, ydata, next_count
