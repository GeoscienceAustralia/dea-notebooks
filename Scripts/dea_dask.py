## dea_dask.py
'''
Description: A set of python functions for simplifying the creation of a 
local dask cluster.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data 
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on 
Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Functions included:
    create_local_dask_cluster
    
Last modified: February 2020

'''


import os
import dask
from dask.utils import parse_bytes
from datacube.utils.dask import start_local_dask
from datacube.utils.rio import configure_s3_access


def create_local_dask_cluster(spare_mem='3Gb'):
    """
    Using the datacube utils function 'start_local_dask', generate
    a local dask cluster. Automatically detects if on AWS or NCI
    
    Parameters
    ----------  
    spare_mem : String, optional
        The amount of memory, in Gb, to leave for the notebook to run.
        This memory will not be used by the cluster. e.g '3Gb'
    
    """

    if 'AWS_ACCESS_KEY_ID' in os.environ:
        
        # close previous client if any
        client = locals().get('client', None)
        if client is not None:
            client.close()
            del client
        
        # configure dashboard link to go over proxy
        dask.config.set({"distributed.dashboard.link":
                     os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')+"proxy/{port}/status"})
                
        # start up a local cluster  
        client = start_local_dask(mem_safety_margin=spare_mem)

        ## Configure GDAL for s3 access
        configure_s3_access(aws_unsigned=True,  
                            client=client);
    else:        
        
        # close previous client if any
        client = locals().get('client', None)
        if client is not None:
            client.close()
            del client
            
        # start up a local cluster on NCI
        client = start_local_dask(mem_safety_margin=spare_mem)

    # show the dask cluster settings
    display(client)