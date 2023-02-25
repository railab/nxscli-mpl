"""Module containing the Click types for nxscli-mpl."""

from typing import Any

import click
from nxscli.cli.types import (
    Channels,
    StringList2,
    Trigger,
    channels_option_help,
    trigger_option_help,
)

###############################################################################
# Globals: stirngs
###############################################################################


fmt_option_help = """Plugin specific Matplotlib format string configuration.
                     Channels separated by a semicolon (;),
                     vectors separated by a commas (?).
                     Example: 'r?g?b; -r?; r?b'
                     Defalut: Matplotlib default.
                      """  # noqa: D301


###############################################################################
# Decorator: plot_options
###############################################################################


# common plot options
_plot_options = (
    click.option(
        "--chan",
        default=None,
        type=Channels(),
        help=channels_option_help,
    ),
    click.option(
        "--trig",
        default=None,
        type=Trigger(),
        help=trigger_option_help,
    ),
    click.option("--dpi", type=int, default=100),
    click.option(
        "--fmt",
        default="",
        type=StringList2(ch1="?"),
        help=fmt_option_help,
    ),
    click.option("--write", type=click.Path(resolve_path=False), default=""),
)


def plot_options(fn: Any) -> Any:
    """Decorate command with common plot options decorator."""
    for decorator in reversed(_plot_options):
        fn = decorator(fn)
    return fn
