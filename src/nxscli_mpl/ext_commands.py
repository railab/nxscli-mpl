"""Matplotlib extension commands."""

from typing import TYPE_CHECKING

from nxscli_mpl.commands.cmd_ani1 import cmd_pani1
from nxscli_mpl.commands.cmd_ani2 import cmd_pani2
from nxscli_mpl.commands.cmd_cap import cmd_pcap
from nxscli_mpl.commands.config.cmd_mpl import cmd_mpl

if TYPE_CHECKING:
    import click

commands_list: list["click.Command"] = [
    cmd_mpl,
    cmd_pcap,
    cmd_pani1,
    cmd_pani2,
]
