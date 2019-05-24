import datacube
from datetime import datetime
current_time = datetime.now()
dc = datacube.Datacube()
lat, lon = -33.324, 149.09
time_period = ('2019-02-01', current_time.strftime('%m/%d/%Y'))
query = {'time': time_period}
datasets= dc.find_datasets(product='wofs_albers', **query)
#datasets= dc.find_datasets(product='ls8_nbart_albers', **query)
dataset_times = [dataset.center_time for dataset in datasets]
dataset_times.sort()
print(dataset_times[-1])