from unittest import mock

import matplotlib
import matplotlib.pyplot as plt
import pytest  # type: ignore

import nxscli_mpl


def pytest_sessionstart(session):
    # force no TK gui
    matplotlib.use("Agg")


@pytest.fixture(scope="session", autouse=True)
def default_session_fixture(request):
    # mock MplManager show method
    patched = mock.patch.object(
        nxscli_mpl.plot_mpl.MplManager, "show", autospec=True
    )
    patched.start()

    def unpatch():
        patched.stop()

    request.addfinalizer(unpatch)


@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Keep pyplot state isolated across tests."""
    plt.close("all")
    yield
    plt.close("all")
