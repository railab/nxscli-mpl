from nxscli_mpl.plugins.roll import PluginRoll


def test_plugin_roll_init() -> None:
    plugin = PluginRoll()

    assert plugin.stream is True
    assert plugin.get_plot_handler() is None
    assert plugin.data_wait() is True
