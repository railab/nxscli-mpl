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
        {"maxsamples": 64, "write": "", "hold_after_trigger": False},
    )

    assert isinstance(ani, RollAnimation)
    assert pdata.samples_max == 64
    assert pdata.xlim == (0, 64)
    assert ani._fig is fig
    assert ani._queue_data is qdata


def test_roll_animation_holds_after_trigger_event(mocker) -> None:
    class DummyLine:
        def set_data(self, xdata, ydata) -> None:  # noqa: ANN001
            self.data = (xdata, ydata)

    class DummyPData:
        def __init__(self) -> None:
            self.samples_max = 8
            self.xdata = [[]]
            self.ydata = [[]]
            self.lns = [DummyLine()]
            self.trigger_line = mocker.Mock()
            self.trigger_x = None

        def xdata_extend_max(self, data) -> None:  # noqa: ANN001
            self.xdata[0].extend(data[0])

        def ydata_extend_max(self, data) -> None:  # noqa: ANN001
            self.ydata[0].extend(data[0])

        def set_trigger_marker(self, xpos) -> None:  # noqa: ANN001
            self.trigger_x = xpos

    ani = RollAnimation(
        object(),
        DummyPData(),
        object(),
        "",
        hold_after_trigger=True,
        static_xticks=True,
    )
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()
    mocker.patch.object(ani, "yscale_extend")

    out = ani._animation_update_cmn(
        ([[5, 6]], [[2.0, 3.0]], 6.0), ani._plot_data
    )

    assert out == ani._plot_data.lns + [ani._plot_data.trigger_line]
    ani._ani.event_source.stop.assert_called_once_with()
