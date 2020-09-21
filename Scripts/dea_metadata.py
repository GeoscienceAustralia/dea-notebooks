## dea_metadata.py
'''
Description: This file contains a set of python functions for handling
Digital Earth Australia product metadata.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, file one on
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Functions included:
    cmi_metadata

Last modified: September 2020

'''

# Import required packages
from IPython.display import Markdown
import requests
import json


def cmi_metadata(product=None):
    
    """
    Automatically extract the Geoscience Australia National Earth and
    Marine Observations Content Management Interface (CMI, available at 
    https://cmi.ga.gov.au/) metadata description for a DEA product as 
    markdown-formatted text using the CMI JSON endpoint, and render 
    this into a notebook cell.
    
    
    Parameters
    ----------
    product : string
        An string giving the CMI short name of the product to load 
        metadata description information for. This string is matched up
        to the CMI product ID (e.g. 325 etc) and used to load data using
        CMI's JSON endpoint. The following DEA products are currently 
        supported:
        
            DEA Intertidal Elevation': 325
            DEA Intertidal Extents': 174
            DEA Fractional Cover': 119
            DEA Water Observations': 142
            DEA High and Low Tide Imagery': 133
            DEA Waterbodies': 456
            DEA Coastlines': 581
            
    Returns
    -------
    The CMI "product_abstract", "product_what_this_product_offers", 
    "product_applications", "product_metadata_url", and 
    "product_publications" JSON fields rendered as markdown within a
    Jupyter notebook cell.
    
    """
    
    # Get product CMI ID from name. These allow us to load data using
    # CMI's JSON functionality
    cmi_dict = {'DEA Intertidal Elevation': 325,
                'DEA Intertidal Extents': 174,
                'DEA Fractional Cover': 119,
                'DEA Water Observations': 142,
                'DEA High and Low Tide Imagery': 133,
                'DEA Waterbodies': 456,
                'DEA Coastlines': 581}
    
    # Raise error if product is not contained in dictionary keys
    try:
        cmi_id = cmi_dict[product]
    except KeyError:
        raise TypeError(f'Please provide a DEA product name from '
              f'the following list to `product`:\n\n{list(cmi_dict.keys())}')
       
    # Load JSON metadata
    json_url = f'https://cmi.ga.gov.au/api/v1/data-product/json/{cmi_id}?_format=json'
    response = json.loads(requests.get(json_url).text)[0]
    
    # Extract metadata
    abstract = response["product_abstract"]
    product_offers = response["product_what_this_product_offers"]
    product_apps = response["product_applications"]
    product_url = response["product_metadata_url"]
    
    # Set publications string based on if publications exist
    product_pubs = response["product_publications"]
    product_pubs = f'### Publications\n * {product_pubs}' if product_pubs else ''
    
    # Create markdown string to plot    
    markdown_str = f'## {product}\n' \
                   f'### Background\n{abstract}\n\n' \
                   f'### What this product offers\n{product_offers}\n\n' \
                   f'### Applications\n{product_apps}\n\n' \
                   f'{product_pubs}\n\n' \
                   f'> **Note:** For more technical information about the ' \
                   f'{product} product, visit the official [Geoscience ' \
                   f'Australia {product} product description.]({product_url})\n\n' \
                   f'<img align="left" src="{response["product_header_image"]}" width="250" style="padding-left: 20px;">'

    # Strip out non-compatible code
    markdown_str = markdown_str.replace(' lang="EN-US" xml:lang="EN-US" xml:lang="EN-US"', '')
    
    return Markdown(markdown_str)
