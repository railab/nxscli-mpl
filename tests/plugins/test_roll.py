from nxscli_mpl.plugins.roll import PluginRoll, RollAnimation


def test_plugin_roll_init() -> None:
    plugin = PluginRoll()

    assert plugin.stream is True
    assert plugin.get_plot_handler() is None
    assert plugin.data_wait() is True


def test_plugin_roll_start_sets_limits_and_returns_animation() -> None:
    class DummyPData:
        def __init__(self) -> None:
            self.samples_max = 0
            self.xlim = None

        def set_xlim(self, xlim) -> None:
            self.xlim = xlim

    fig = object()
    pdata = DummyPData()
    qdata = object()

    ani = PluginRoll()._start(
        fig,
        pdata,
        qdata,
        {"maxsamples": 64, "write": ""},
    )

    assert isinstance(ani, RollAnimation)
    assert pdata.samples_max == 64
    assert pdata.xlim == (0, 64)
    assert ani._fig is fig
    assert ani._qdata is qdata
