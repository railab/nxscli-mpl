import nxscli_mpl
import nxscli_mpl.plugin


def test_nxsclimpl():
    assert nxscli_mpl.__version__

    assert isinstance(nxscli_mpl.plugin.plugins_list, list)
    assert isinstance(nxscli_mpl.plugin.configs_list, list)
