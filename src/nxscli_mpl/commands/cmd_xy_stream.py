"""Module containing XY stream plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment

from nxscli_mpl.cli.types import plot_options
from nxscli_mpl.commands._common import enable_plot_command

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


@click.command(name="m_xy_live")
@click.argument("window", type=int, required=True)
@click.option("--hop", type=int, default=0, show_default=True)
@click.option(
    "--align-policy",
    type=click.Choice(["truncate"]),
    default="truncate",
    show_default=True,
)
@plot_options
@pass_environment
def cmd_pxy_stream(
    ctx: Environment,
    window: int,
    hop: int,
    align_policy: str,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Windowed streaming XY plot."""
    return enable_plot_command(
        ctx,
        "m_xy_live",
        window=window,
        hop=hop,
        align_policy=align_policy,
        channels=chan,
        trig=trig,
        dpi=dpi,
        fmt=fmt,
        write=write,
    )
