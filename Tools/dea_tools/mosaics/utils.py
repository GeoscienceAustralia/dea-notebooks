from urllib.parse import urlparse
import requests

def _is_s3(path):
    """
    Determine whether output location is on S3.
    """
    uu = urlparse(path)
    return uu.scheme == "s3"


def _get_vsicurlhttp_from_s3(s3_url):
    """
    Convert an S3 URL to a GDAL-compatible /vsicurl/ HTTPS path.
    """
    
    if "dea-public-data-dev/" in s3_url:
        return s3_url.replace(
            "dea-public-data-dev/",
            "/vsicurl/https://dea-public-data-dev.s3-ap-southeast-2.amazonaws.com/"
        )
    elif "dea-public-data/" in s3_url:
        return s3_url.replace(
            "dea-public-data/",
            "/vsicurl/https://data.dea.ga.gov.au/"
        )
    else:
        raise ValueError(f"Unexpected S3 URL structure: {s3_url}")


def _get_vsis3_from_s3(s3_url):
    """
    Convert an S3 URI to a GDAL-compatible /vsis3/ path.
    """
    return "/vsis3/" + s3_url


def _file_exists_s3(url):
    """
    Return True if the remote file exists at the given /vsicurl/ or HTTPS URL.
    Specifically used for files in S3
    """
    if url.startswith("/vsicurl/"):
        url = url.replace("/vsicurl/", "")
    response = requests.head(url)
    return response.status_code == 200


def _clean_label_dict(label):
    """
    Clean and standardize label strings.
    It might be needed for the land cover colour scheme dictionaries
    """
    label = label.replace(">", "more than")
    label = label.replace("<", "less than")
    label = label.replace(":", "")
    label = label.replace("\n", "")
    return label
    
