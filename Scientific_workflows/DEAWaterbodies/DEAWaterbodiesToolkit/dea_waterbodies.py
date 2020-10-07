"""Functions for working with DEA Waterbodies.

License: The code in this module is licensed under the Apache License,
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
    load_waterbody

Last modified: September 2020
"""

import pandas as pd

WATERBODIES_CSV_URL = 'https://data.dea.ga.gov.au/projects/WaterBodies/timeseries'

def load_waterbody(uid, csv_path=WATERBODIES_CSV_URL):
    """Load a waterbody time series.
    
    Parameters
    ----------
    uid : str
        UID/geohash of waterbody.
    
    csv_path : str
        Path to the folder containing waterbodies CSVs.
        Optional. Defaults to the online version.
        
    Returns
    -------
    pd.DataFrame
    """
    csv_path = f"{csv_path}/{uid[:4]}/{uid}.csv"

    # Load the data using `pandas`:
    time_series = pd.read_csv(csv_path, 
                              header=0,
                              names=["date", "pc_wet", "px_wet"],
                              parse_dates=["date"],
                              index_col="date",
                             )

    # Convert percentages into a float between 0 and 1.
    time_series.pc_wet /= 100
    
    return time_series
