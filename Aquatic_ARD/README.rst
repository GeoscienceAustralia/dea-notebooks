.. Notebook Gallery Instructions:



Digital Earth Australia Aquatic ARD Test Database
######################################################


.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
  :target: https://opensource.org/licenses/Apache-2.0
  :alt: Apache license

----------

The accompanying jupyter notebook ``Aquatic_ARD_Access.ipynb`` is to provide access to the test database of Aquatic Analysis Ready data produced by the DEA program for selected inland and coastal locations of Australia.

The notebook should be used in conjunction with the DEA notebooks and tools <https://github.com/GeoscienceAustralia/dea-notebooks> and an experimental sunglint module designed to test a range of sunglint removal options <https://github.com/GeoscienceAustralia/sun-glint-correction>. Instructions of the installation of both repositories can be found in their README documentation, along with extensive users guides and learning material.

**Accessing the DEA Aquatic ARD database**

The database requires access to the r78 project at NCI. To access the database you will need to modify your datacube conf file "~/.datacube.conf", located in your home directory, by appending the following:

.. code-block:: console

    [water-atcor] 
    db_hostname: deadev.nci.org.au
    db_port: 6432
    db_database: water_atcor_samples
    

----------

*Database Coverage and Time Periods*

``Sentinel 2A``

  Zone 50, tile HMJ, data period 2016.12 -2020.12
  
  Zone 52, tile KDG, data period 2016.11 -2020.12
  
  Zone 52, tile LDH, data period 2016.09 -2020.12
  
  Zone 54, tile HXK, data period 2016.12 -2020.12
  
  Zone 55, tile HBT, data period 2016.11 -2020.12
  
  Zone 55, tile HBU, data period 2016.11 -2020.12
  
  Zone 55, tile HCT, data period 2016.11 -2020.12
  
  Zone 55, tile HCU, data period 2016.11 -2020.12
  
  Zone 55, tile HCV, data period 2016.11 -2020.12
  
  Zone 55, tile HEA, data period 2016.04 -2020.12
  
  Zone 55, tile HEV, data period 2016.11 -2020.12
  
  Zone 55, tile HFA, data period 2016.04 -2020.12
  
  Zone 55, tile HFB, data period 2016.04 -2020.12
  
  Zone 55, tile KDT, data period 2016.12 -2020.12
  
  Zone 55, tile KET, data period 2016.12 -2020.12

``Sentinel 2A``


  Zone 50, tile HMJ, data period 2017.07 -2020.12
  
  Zone 52, tile KDG, data period 2017.07 -2020.12
  
  Zone 52, tile LDH, data period 2017.07 -2020.12
  
  Zone 54, tile HXK, data period 2017.07 -2020.12
  
  Zone 55, tile HBT, data period 2017.07 -2020.12
  
  Zone 55, tile HBU, data period 2017.07 -2020.12
  
  Zone 55, tile HCT, data period 2017.07 -2020.12
  
  Zone 55, tile HCU, data period 2017.07 -2020.12
  
  Zone 55, tile HCV, data period 2017.07 -2020.12
  
  Zone 55, tile HEA, data period 2017.07 -2020.12
  
  Zone 55, tile HEV, data period 2017.07 -2020.12
  
  Zone 55, tile HFA, data period 2017.07 -2020.12
  
  Zone 55, tile HFB, data period 2017.07 -2020.12
  
  Zone 55, tile KDT, data period 2017.07 -2020.12
  
  Zone 55, tile KET, data period 2017.07 -2020.12

``Landsat 8``


  Path 91, row 081, data period 2013.04 -2020.12
  
  Path 92, row 084, data period 2013.03 -2020.12
  
  Path 93, row 086, data period 2013.03 -2020.12
  
  Path 94, row 074, data period 2013.04 -2020.12
  
  Path 95, row 082, data period 2013.04 -2020.12
  
  Path 107, row 071, data period 2013.04 -2020.12
  
  Path 112, row 083, data period 2013.04 -2020.12
  










