=====
Usage
=====

Configuratio commands
=====================


* ``mpl`` - Matplotlib configuration.

  Optional, at default:

  - style = "ggplot,fast"


Plugin commands
===============


Plugins supported so far:

* ``m_live`` - infinite animation plot (no X-axis limits)
* ``m_roll`` - animation plot with X-axis saturation
* ``m_snap`` - static plot (capture data and plot)
* ``m_fft`` - static FFT plot
* ``m_fft_live`` - streaming FFT plot
* ``m_hist`` - static histogram plot
* ``m_hist_live`` - streaming histogram plot
* ``m_xy`` - static XY plot
* ``m_xy_live`` - streaming XY plot
* ``m_polar`` - static polar plot
* ``m_polar_live`` - streaming polar plot

For more information, use the plugin's ``--help`` option.


CLI Test Commands
=================

All commands below were validated against ``dummy`` interface.

Important syntax rule for chained commands:

* plugin options must be placed before positional args
  (for example ``m_fft_live --hop 128 512``, not
  ``m_fft_live 512 --hop 128``).

Static plots (save to files)
----------------------------

.. code-block:: bash

   python -m nxscli dummy chan 0 m_snap --write /tmp/nxscope_plot_test/m_snap_static.png 1200
   python -m nxscli dummy chan 9 m_fft --write /tmp/nxscope_plot_test/fft_static.png 2048
   python -m nxscli dummy chan 0 m_hist --bins 64 --write /tmp/nxscope_plot_test/hist_static.png 2000
   python -m nxscli dummy chan 0,2 m_xy --write /tmp/nxscope_plot_test/xy_static.png 1500
   python -m nxscli dummy chan 15 m_xy --write /tmp/nxscope_plot_test/xy_static_vdim2.png 1500
   python -m nxscli dummy chan 0,2 m_polar --write /tmp/nxscope_plot_test/polar_static.png 1500
   python -m nxscli dummy chan 16 m_polar --write /tmp/nxscope_plot_test/polar_static_vdim2.png 1500

Streaming plots
---------------

.. code-block:: bash

   python -m nxscli dummy chan 0 m_live
   python -m nxscli dummy chan 0 m_roll 512
   python -m nxscli dummy chan 9 m_fft_live --hop 128 512
   python -m nxscli dummy chan 0 m_hist_live --hop 128 --bins 64 512
   python -m nxscli dummy chan 0,2 m_xy_live --hop 128 512
   python -m nxscli dummy chan 15 m_xy_live --hop 128 512
   python -m nxscli dummy chan 0,2 m_polar_live --hop 128 512
   python -m nxscli dummy chan 16 m_polar_live --hop 128 512

For automated smoke checks in CI/shell, you can use timeout:

.. code-block:: bash

   timeout 8 python -m nxscli dummy chan 0 m_live
   timeout 8 python -m nxscli dummy chan 0 m_roll 512
   timeout 8 python -m nxscli dummy chan 9 m_fft_live --hop 128 512
   timeout 8 python -m nxscli dummy chan 0 m_hist_live --hop 128 --bins 64 512
   timeout 8 python -m nxscli dummy chan 0,2 m_xy_live --hop 128 512
   timeout 8 python -m nxscli dummy chan 15 m_xy_live --hop 128 512
   timeout 8 python -m nxscli dummy chan 0,2 m_polar_live --hop 128 512

Matplotlib config command
-------------------------

.. code-block:: bash

   python -m nxscli dummy mpl --style classic chan 0 m_snap --write /tmp/nxscope_plot_test/m_snap_classic.png 300
