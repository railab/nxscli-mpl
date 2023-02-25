import nxscli_mpl
import nxscli_mpl.ext_commands
import nxscli_mpl.ext_plugins


def test_nxsclimpl():
    assert nxscli_mpl.__version__

    assert isinstance(nxscli_mpl.ext_plugins.plugins_list, list)
    assert isinstance(nxscli_mpl.ext_commands.commands_list, list)
