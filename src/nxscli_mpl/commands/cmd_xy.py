"""Module containing XY plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment
from nxscli.cli.types import Samples

from nxscli_mpl.cli.types import plot_options
from nxscli_mpl.commands._common import enable_plot_command

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


@click.command(name="m_xy")
@click.argument("samples", type=Samples(), required=True)
@plot_options
@pass_environment
def cmd_pxy(
    ctx: Environment,
    samples: int,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Static XY plot for a given number of samples."""
    return enable_plot_command(
        ctx,
        "m_xy",
        samples=samples,
        channels=chan,
        trig=trig,
        dpi=dpi,
        fmt=fmt,
        write=write,
    )
