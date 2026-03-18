from nxscli_mpl.plugins.live import PluginLive


def test_plugin_live_init() -> None:
    plugin = PluginLive()

    assert plugin.stream is True
    assert plugin.get_plot_handler() is None
    assert plugin.data_wait() is True
