"""Module containing animation2 plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment

from nxscli_mpl.cli.types import plot_options
from nxscli_mpl.commands._common import enable_plot_command

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


###############################################################################
# Command: cmd_m_roll
###############################################################################


@click.command(name="m_roll")
@click.argument("maxsamples", type=int, required=True)
@plot_options
@pass_environment
def cmd_m_roll(
    ctx: Environment,
    maxsamples: int,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Animation plot with a lenght limit (saturated X-axis)."""
    return enable_plot_command(
        ctx,
        "m_roll",
        maxsamples=maxsamples,
        channels=chan,
        trig=trig,
        dpi=dpi,
        fmt=fmt,
        write=write,
    )
