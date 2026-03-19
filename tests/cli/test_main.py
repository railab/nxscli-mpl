import nxscli
import pytest  # type: ignore
from click.testing import CliRunner
from nxscli.cli.main import main


@pytest.fixture
def enable_plugin(mocker):
    return mocker.patch(
        "nxscli.phandler.PluginHandler.enable",
        autospec=True,
        return_value=True,
    )


@pytest.fixture
def runner(mocker, enable_plugin):
    mocker.patch.object(nxscli.cli.main, "wait_for_plugins", autospec=True)
    return CliRunner()


def test_main_mpl(runner):
    args = ["dummy", "mpl"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_m_snap(runner):
    args = ["chan", "1", "m_snap", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    # args = ["dummy", "m_snap", "1"]
    # result = runner.invoke(main, args)
    # assert result.exit_code == 1

    args = ["dummy", "chan", "1", "m_snap", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1", "m_snap", "1000"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_m_live(runner):
    args = ["chan", "1", "m_live"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "1", "m_live"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "1", "m_live"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_m_roll(runner):
    args = ["chan", "1", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    # args = ["dummy", "m_roll", "1"]
    # result = runner.invoke(main, args)
    # assert result.exit_code == 1

    args = ["dummy", "chan", "1", "m_roll"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "1", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pfft(runner):
    args = ["chan", "1", "m_fft", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "11", "m_fft", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_phist(runner):
    args = ["chan", "1", "m_hist", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "13", "m_hist", "--bins", "16", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pxy(runner):
    args = ["chan", "1", "m_xy", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "15,16", "m_xy", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "15", "m_xy", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pfft_stream(runner):
    args = ["chan", "1", "m_fft_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "11", "m_fft_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_phist_stream(runner):
    args = ["chan", "1", "m_hist_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "13", "m_hist_live", "--bins", "16", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pxy_stream(runner):
    args = ["chan", "1", "m_xy_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "15,16", "m_xy_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "15", "m_xy_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_mpolar(runner):
    args = ["chan", "1", "m_polar", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "0,2", "m_polar", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "16", "m_polar", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_mpolar_stream(runner):
    args = ["chan", "1", "m_polar_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "0,2", "m_polar_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "16", "m_polar_live", "128"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_dispatch_fft_special_channel(runner, enable_plugin):
    patched = enable_plugin
    args = ["dummy", "chan", "11", "m_fft", "64"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert patched.call_count == 1
    assert patched.call_args.args[1] == "m_fft"
    assert patched.call_args.kwargs["channels"] is None


def test_main_dispatch_hist_special_channel(runner, enable_plugin):
    patched = enable_plugin
    args = ["dummy", "chan", "13", "m_hist_live", "--bins", "16", "64"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert patched.call_count == 1
    assert patched.call_args.args[1] == "m_hist_live"
    assert patched.call_args.kwargs["channels"] is None


def test_main_dispatch_xy_special_channels(runner, enable_plugin):
    patched = enable_plugin
    args = ["dummy", "chan", "15,16", "m_xy_live", "64"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert patched.call_count == 1
    assert patched.call_args.args[1] == "m_xy_live"
    assert patched.call_args.kwargs["channels"] is None


def test_main_dispatch_m_snap_interactive(runner, enable_plugin):
    patched = enable_plugin
    args = ["dummy", "chan", "1", "m_snap", "i"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert patched.call_count == 1
    assert patched.call_args.args[1] == "m_snap"
    assert patched.call_args.kwargs["samples"] == -1
    assert "nostop" not in patched.call_args.kwargs


def test_main_trig_mpl(runner):
    args = ["dummy", "chan", "1", "trig", "xxx", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "x=1", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "g=1", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "g:on", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1", "trig", "g:off", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1,2", "trig", "1:on;2:off", "m_roll", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1,2,3", "m_roll", "--trig", "2:off", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = [
        "dummy",
        "chan",
        "1,2,3",
        "trig",
        "g:er#2@0,0,10,100",
        "m_snap",
        "100",
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
