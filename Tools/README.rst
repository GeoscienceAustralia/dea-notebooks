dea-tools
=========

Python functions and algorithms for developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning).

Installation
------------

To work with this module on the DEA Sandbox from within the `dea-notebooks` repo, you can add the Tools folder to the system path:

.. code-block:: python
   :linenos:

   import sys
   sys.path.insert(1, '../Tools/')
   import dea_tools.datahandling  # or some other submodule

You can also `pip install` the module. To do this on the DEA Sandbox, run `pip` from the terminal:

.. code-block:: bash
   pip install -e Tools/

Install from the source on any other system with `pip`:

.. code-block:: bash
    pip install git+https://github.com/GeoscienceAustralia/dea-notebooks.git#subdirectory=Tools
