import nxscli
import pytest  # type: ignore
from click.testing import CliRunner
from nxscli.cli.main import main


@pytest.fixture
def runner(mocker):
    mocker.patch.object(nxscli.cli.main, "wait_for_plugins", autospec=True)
    return CliRunner()


def test_main_mpl(runner):
    args = ["dummy", "mpl"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pcap(runner):
    args = ["chan", "1", "pcap", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    # args = ["dummy", "pcap", "1"]
    # result = runner.invoke(main, args)
    # assert result.exit_code == 1

    args = ["dummy", "chan", "1", "pcap", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1", "pcap", "1000"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pani1(runner):
    args = ["chan", "1", "pani1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "1", "pani1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "1", "pani1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_pani2(runner):
    args = ["chan", "1", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    # args = ["dummy", "pani2", "1"]
    # result = runner.invoke(main, args)
    # assert result.exit_code == 1

    args = ["dummy", "chan", "1", "pani2"]
    result = runner.invoke(main, args)
    assert result.exit_code == 2

    args = ["dummy", "chan", "1", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0


def test_main_trig_mpl(runner):
    args = ["dummy", "chan", "1", "trig", "xxx", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "x=1", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "g=1", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 1

    args = ["dummy", "chan", "1", "trig", "g:on", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1", "trig", "g:off", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1,2", "trig", "1:on;2:off", "pani2", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = ["dummy", "chan", "1,2,3", "pani2", "--trig", "2:off", "1"]
    result = runner.invoke(main, args)
    assert result.exit_code == 0

    args = [
        "dummy",
        "chan",
        "1,2,3",
        "trig",
        "g:er#2@0,0,10,100",
        "pcap",
        "100",
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 0
