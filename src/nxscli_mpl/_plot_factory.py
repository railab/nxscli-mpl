"""Private mpl plot factory helpers."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nxscli.idata import PluginDataCb
    from nxscli.trigger import TriggerHandler
    from nxslib.dev import DeviceChannel

    from nxscli_mpl.plot_mpl import PluginPlotMpl


def create_plot_surface(
    chanlist: list["DeviceChannel"],
    trig: list["TriggerHandler"],
    cb: "PluginDataCb",
    dpi: float = 100.0,
    fmt: list[str] | None = None,
    mode: str = "detached",
    parent: Any = None,
) -> "PluginPlotMpl":
    """Create plot surface in detached or attached mode."""
    from nxscli_mpl.plot_mpl import PluginPlotMpl

    return PluginPlotMpl(
        chanlist=chanlist,
        trig=trig,
        cb=cb,
        dpi=dpi,
        fmt=fmt,
        mode=mode,
        parent=parent,
    )


def build_plot_surface(
    phandler: Any,
    kwargs: dict[str, Any],
) -> "PluginPlotMpl":
    """Build plot surface from plugin handler and runtime kwargs."""
    chanlist = phandler.chanlist_plugin(kwargs["channels"])
    trig = phandler.triggers_plugin(chanlist, kwargs["trig"])
    cb = phandler.cb_get()
    return create_plot_surface(
        chanlist=chanlist,
        trig=trig,
        cb=cb,
        dpi=kwargs["dpi"],
        fmt=kwargs["fmt"],
        mode=str(kwargs.get("plot_mode", "detached")),
        parent=kwargs.get("plot_parent"),
    )
