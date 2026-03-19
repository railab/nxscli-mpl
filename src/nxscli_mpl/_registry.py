"""Private backend registry definitions."""

from typing import TYPE_CHECKING, Any, cast

from nxscli.iplugin import DPluginDescription

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
from nxscli_mpl.plugins._typed_windowed import (
    PluginFftStream,
    PluginHistStream,
    PluginPolarStream,
    PluginXyStream,
)
from nxscli_mpl.plugins.fft import PluginFft
from nxscli_mpl.plugins.histogram import PluginHistogram
from nxscli_mpl.plugins.live import PluginLive
from nxscli_mpl.plugins.polar import PluginPolar
from nxscli_mpl.plugins.roll import PluginRoll
from nxscli_mpl.plugins.snap import PluginSnap
from nxscli_mpl.plugins.xy import PluginXy

if TYPE_CHECKING:
    import click
    from nxscli.iplugin import IPlugin


COMMANDS: tuple["click.Command", ...] = (
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
)

PLUGIN_TYPES: tuple[tuple[str, type["IPlugin"]], ...] = (
    ("m_snap", cast("type[Any]", PluginSnap)),
    ("m_live", PluginLive),
    ("m_roll", PluginRoll),
    ("m_fft", cast("type[Any]", PluginFft)),
    ("m_hist", cast("type[Any]", PluginHistogram)),
    ("m_xy", cast("type[Any]", PluginXy)),
    ("m_polar", cast("type[Any]", PluginPolar)),
    ("m_fft_live", PluginFftStream),
    ("m_hist_live", PluginHistStream),
    ("m_xy_live", PluginXyStream),
    ("m_polar_live", PluginPolarStream),
)


def build_commands_list() -> list["click.Command"]:
    """Return the exported backend command list."""
    return list(COMMANDS)


def build_plugins_list() -> list[DPluginDescription]:
    """Return the exported backend plugin list."""
    return [DPluginDescription(name, plugin) for name, plugin in PLUGIN_TYPES]
