import nxscli_mpl
import nxscli_mpl.ext_commands
import nxscli_mpl.ext_plugins


def test_nxsclimpl():
    assert nxscli_mpl.__version__

    assert isinstance(nxscli_mpl.ext_plugins.plugins_list, list)
    assert isinstance(nxscli_mpl.ext_commands.commands_list, list)
    assert [cmd.name for cmd in nxscli_mpl.ext_commands.commands_list] == [
        "mpl",
        "m_snap",
        "m_live",
        "m_roll",
        "m_fft",
        "m_hist",
        "m_xy",
        "m_polar",
        "m_fft_live",
        "m_hist_live",
        "m_xy_live",
        "m_polar_live",
    ]
    assert [plugin.name for plugin in nxscli_mpl.ext_plugins.plugins_list] == [
        "m_snap",
        "m_live",
        "m_roll",
        "m_fft",
        "m_hist",
        "m_xy",
        "m_polar",
        "m_fft_live",
        "m_hist_live",
        "m_xy_live",
        "m_polar_live",
    ]
