"""Module containing histogram plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment
from nxscli.cli.types import Samples

from nxscli_mpl.cli.types import plot_options

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


@click.command(name="m_hist")
@click.argument("samples", type=Samples(), required=True)
@click.option("--bins", type=int, default=32, show_default=True)
@plot_options
@pass_environment
def cmd_phist(
    ctx: Environment,
    samples: int,
    bins: int,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Static histogram plot for a given number of samples."""
    assert ctx.phandler
    if samples == 0:  # pragma: no cover
        ctx.waitenter = True

    ctx.phandler.enable(
        "m_hist",
        samples=samples,
        bins=bins,
        channels=chan,
        trig=trig,
        dpi=dpi,
        fmt=fmt,
        write=write,
        nostop=ctx.waitenter,
    )

    ctx.needchannels = True
    return True
