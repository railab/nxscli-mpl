"""Module containing animation1 plugin command."""

from typing import TYPE_CHECKING

import click
from nxscli.cli.environment import Environment, pass_environment

from nxscli_mpl.cli.types import plot_options
from nxscli_mpl.commands._common import enable_plot_command

if TYPE_CHECKING:
    from nxscli.trigger import DTriggerConfigReq


###############################################################################
# Command: cmd_m_live
###############################################################################


@click.command(name="m_live")
@click.option(
    "--hold-post-samples",
    type=int,
    default=0,
    show_default=True,
    help="Keep updating this many samples after the trigger before hold.",
)
@plot_options
@pass_environment
def cmd_m_live(
    ctx: Environment,
    hold_post_samples: int,
    chan: list[int],
    trig: dict[int, "DTriggerConfigReq"],
    dpi: float,
    hold_after_trigger: bool,
    fmt: list[list[str]],
    write: str,
) -> bool:
    """[plugin] Animation plot without a length limit (infinite plot)."""
    return enable_plot_command(
        ctx,
        "m_live",
        channels=chan,
        trig=trig,
        dpi=dpi,
        hold_after_trigger=hold_after_trigger,
        hold_post_samples=hold_post_samples,
        fmt=fmt,
        write=write,
    )
