dea-tools
=========

Python functions and algorithms for developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning).

Installation
------------

To work with this module on the DEA Sandbox from within the `dea-notebooks` repo, you can add the Tools folder to the system path:

.. code-block:: python

   import sys
   sys.path.insert(1, '../Tools/')
   import dea_tools.datahandling  # or some other submodule

You can also `pip install` the module. To do this on the DEA Sandbox, run `pip` from the terminal:

.. code-block:: bash

   pip install -e Tools/

Install from the source on any other system with `pip`:

.. code-block:: bash

    pip install --extra-index-url="https://packages.dea.ga.gov.au" git+https://github.com/GeoscienceAustralia/dea-notebooks.git#subdirectory=Tools

Citing DEA Tools
----------------

If you use any of the notebooks, code or tools in this repository in your work, please reference them using the following citation:

    Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger, M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A., Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth Australia notebooks and tools repository. Geoscience Australia, Canberra. https://doi.org/10.26186/145234

