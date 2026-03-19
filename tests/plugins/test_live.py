from nxscli_mpl.plugins.live import LiveAnimation, PluginLive


def test_plugin_live_init() -> None:
    plugin = PluginLive()

    assert plugin.stream is True
    assert plugin.get_plot_handler() is None
    assert plugin.data_wait() is True


def test_live_animation_start_builds_common_animation() -> None:
    fig = object()
    pdata = object()
    qdata = object()

    ani = PluginLive()._start(fig, pdata, qdata, {"write": ""})

    assert isinstance(ani, LiveAnimation)
    assert ani._fig is fig
    assert ani._pdata is pdata
    assert ani._qdata is qdata
    assert ani._writer is None
