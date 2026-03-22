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

    ani = PluginLive()._start(
        fig, pdata, qdata, {"write": "", "hold_after_trigger": False}
    )

    assert isinstance(ani, LiveAnimation)
    assert ani._fig is fig
    assert ani._plot_data is pdata
    assert ani._queue_data is qdata
    assert ani._writer is None


def test_live_animation_holds_after_trigger_event(mocker) -> None:
    class DummyLine:
        def set_data(self, xdata, ydata) -> None:  # noqa: ANN001
            self.data = (xdata, ydata)

    class DummyPData:
        def __init__(self) -> None:
            self.xdata = [[]]
            self.ydata = [[]]
            self.lns = [DummyLine()]
            self.trigger_line = mocker.Mock()
            self.trigger_x = None

        def xdata_extend(self, data) -> None:  # noqa: ANN001
            self.xdata[0].extend(data[0])

        def ydata_extend(self, data) -> None:  # noqa: ANN001
            self.ydata[0].extend(data[0])

        def set_trigger_marker(self, xpos) -> None:  # noqa: ANN001
            self.trigger_x = xpos

    ani = LiveAnimation(
        object(),
        DummyPData(),
        object(),
        "",
        hold_after_trigger=True,
    )
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()
    mocker.patch.object(ani, "yscale_extend")
    mocker.patch.object(ani, "xscale_extend")

    out = ani._animation_update_cmn(
        ([[0, 1]], [[2.0, 3.0]], 1.0), ani._plot_data
    )

    assert out == ani._plot_data.lns + [ani._plot_data.trigger_line]
    ani._ani.event_source.stop.assert_called_once_with()


def test_live_animation_skip_hold_without_trigger(mocker) -> None:
    ani = LiveAnimation(
        object(), object(), object(), "", hold_after_trigger=True
    )
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()

    ani._hold_on_trigger(([], [], None))

    ani._ani.event_source.stop.assert_not_called()


def test_live_animation_skip_hold_without_animation_handle() -> None:
    ani = LiveAnimation(
        object(), object(), object(), "", hold_after_trigger=True
    )

    ani._hold_on_trigger(([[0.0]], [[1.0]], 1.0))

    assert ani._held_on_trigger is True


def test_live_animation_hold_requests_canvas_redraw(mocker) -> None:
    fig = mocker.Mock()
    fig.canvas = mocker.Mock()
    ani = LiveAnimation(fig, object(), object(), "", hold_after_trigger=True)

    ani._hold_on_trigger(([[0.0]], [[1.0]], 1.0))

    fig.canvas.draw_idle.assert_called_once_with()


def test_live_animation_waits_for_hold_post_samples(mocker) -> None:
    fig = mocker.Mock()
    fig.canvas = mocker.Mock()
    ani = LiveAnimation(
        fig,
        object(),
        object(),
        "",
        hold_after_trigger=True,
        hold_post_samples=4,
    )
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()

    ani._hold_on_trigger(([[1.0, 2.0, 3.0]], [[0.0]], 1.0))
    ani._ani.event_source.stop.assert_not_called()

    ani._hold_on_trigger(([[1.0, 2.0, 3.0, 4.0, 5.0]], [[0.0]], None))
    ani._ani.event_source.stop.assert_called_once_with()


def test_live_animation_hold_post_waits_for_non_empty_xdata(mocker) -> None:
    fig = mocker.Mock()
    fig.canvas = mocker.Mock()
    ani = LiveAnimation(
        fig,
        object(),
        object(),
        "",
        hold_after_trigger=True,
        hold_post_samples=4,
    )
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()

    ani._hold_on_trigger(([], [[0.0]], 1.0))

    ani._ani.event_source.stop.assert_not_called()


def test_live_animation_skip_hold_when_already_held(mocker) -> None:
    fig = mocker.Mock()
    fig.canvas = mocker.Mock()
    ani = LiveAnimation(fig, object(), object(), "", hold_after_trigger=True)
    ani._ani = mocker.Mock()
    ani._ani.event_source = mocker.Mock()
    ani._held_on_trigger = True

    ani._hold_on_trigger(([[1.0]], [[0.0]], 1.0))

    ani._ani.event_source.stop.assert_not_called()
