from nxscli_mpl.cli.types import plot_options


def test_plotoptions():
    @plot_options
    def test():
        pass

    test()
