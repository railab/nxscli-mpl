"""Matplotlib extension plugins."""

from nxscli.iplugin import DPluginDescription

from nxscli_mpl.plugins.animation1 import PluginAnimation1
from nxscli_mpl.plugins.animation2 import PluginAnimation2
from nxscli_mpl.plugins.capture import PluginCapture

plugins_list = [
    DPluginDescription("capture", PluginCapture),
    DPluginDescription("animation1", PluginAnimation1),
    DPluginDescription("animation2", PluginAnimation2),
]
