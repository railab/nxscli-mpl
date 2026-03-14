"""Matplotlib extension plugins."""

from typing import Any, cast

from nxscli.iplugin import DPluginDescription

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

plugins_list = [
    DPluginDescription("m_snap", cast("type[Any]", PluginSnap)),
    DPluginDescription("m_live", PluginLive),
    DPluginDescription("m_roll", PluginRoll),
    DPluginDescription("m_fft", cast("type[Any]", PluginFft)),
    DPluginDescription("m_hist", cast("type[Any]", PluginHistogram)),
    DPluginDescription("m_xy", cast("type[Any]", PluginXy)),
    DPluginDescription("m_polar", cast("type[Any]", PluginPolar)),
    DPluginDescription("m_fft_live", PluginFftStream),
    DPluginDescription("m_hist_live", PluginHistStream),
    DPluginDescription("m_xy_live", PluginXyStream),
    DPluginDescription("m_polar_live", PluginPolarStream),
]
