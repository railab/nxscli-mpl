from nxscli_mpl.plugins.roll import PluginRoll


def test_pluginanimaton2_init():
    plugin = PluginRoll()

    assert plugin.stream is True

    # TODO:
