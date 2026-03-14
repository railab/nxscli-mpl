from nxscli_mpl.plugins.live import PluginLive


def test_pluginanimaton1_init():
    plugin = PluginLive()

    assert plugin.stream is True

    # TODO:
