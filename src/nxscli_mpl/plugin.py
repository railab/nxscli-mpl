"""Matplotlib based plugins list."""

from nxscli.iplugin import DPluginDescription

from nxscli_mpl.commands.cmd_ani1 import cmd_pani1
from nxscli_mpl.commands.cmd_ani2 import cmd_pani2
from nxscli_mpl.commands.cmd_cap import cmd_pcap
from nxscli_mpl.commands.config.cmd_mpl import cmd_mpl
from nxscli_mpl.plugins.animation1 import PluginAnimation1
from nxscli_mpl.plugins.animation2 import PluginAnimation2
from nxscli_mpl.plugins.capture import PluginCapture

plugins_list = [
    DPluginDescription("capture", PluginCapture, cmd_pcap),
    DPluginDescription("animation1", PluginAnimation1, cmd_pani1),
    DPluginDescription("animation2", PluginAnimation2, cmd_pani2),
]

configs_list = [cmd_mpl]
