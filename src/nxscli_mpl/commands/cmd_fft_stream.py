"""Module containing FFT stream plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment

from nxscli_mpl.cli.types import plot_options
from nxscli_mpl.commands._common import enable_plot_command

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


@click.command(name="m_fft_live")
@click.argument("window", type=int, required=True)
@click.option("--hop", type=int, default=0, show_default=True)
@click.option("--window-fn", type=str, default="hann", show_default=True)
@plot_options
@pass_environment
def cmd_pfft_stream(
    ctx: Environment,
    window: int,
    hop: int,
    window_fn: str,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Windowed streaming FFT plot."""
    return enable_plot_command(
        ctx,
        "m_fft_live",
        window=window,
        hop=hop,
        window_fn=window_fn,
        channels=chan,
        trig=trig,
        dpi=dpi,
        fmt=fmt,
        write=write,
    )
