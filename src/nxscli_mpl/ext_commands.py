"""Matplotlib extension commands."""

from typing import TYPE_CHECKING

from nxscli_mpl.commands.cmd_ani1 import cmd_m_live
from nxscli_mpl.commands.cmd_ani2 import cmd_m_roll
from nxscli_mpl.commands.cmd_cap import cmd_m_snap
from nxscli_mpl.commands.cmd_fft import cmd_pfft
from nxscli_mpl.commands.cmd_fft_stream import cmd_pfft_stream
from nxscli_mpl.commands.cmd_hist import cmd_phist
from nxscli_mpl.commands.cmd_hist_stream import cmd_phist_stream
from nxscli_mpl.commands.cmd_polar import cmd_mpolar
from nxscli_mpl.commands.cmd_polar_stream import cmd_mpolar_stream
from nxscli_mpl.commands.cmd_xy import cmd_pxy
from nxscli_mpl.commands.cmd_xy_stream import cmd_pxy_stream
from nxscli_mpl.commands.config.cmd_mpl import cmd_mpl

if TYPE_CHECKING:
    import click

commands_list: list["click.Command"] = [
    cmd_mpl,
    cmd_m_snap,
    cmd_m_live,
    cmd_m_roll,
    cmd_pfft,
    cmd_phist,
    cmd_pxy,
    cmd_mpolar,
    cmd_pfft_stream,
    cmd_phist_stream,
    cmd_pxy_stream,
    cmd_mpolar_stream,
]
