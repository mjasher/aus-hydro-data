import os
import json
import numpy
import csv
import datetime
import re
import zipfile
import matplotlib.pylab as plt

"""

The Kister's API is broken. 

eg.
http://data.water.vic.gov.au/cgi/webservice.server.pl?{"function":"get_ts_traces","version":2,"params":{"end_time":"20150831000000","varfrom":"141.00","site_list":"406219","data_type":"mean","multiplier":"1","start_time":"19860514000000","interval":"day","varto":"141.00","datasource":"A"}}
fetches nothing
while the data exists at http://data.water.vic.gov.au/monitoring.htm

So download the necessary sites and water level (100.00) and flow (141.00) manually.

"""

from fetch_data import utils 
from fetch_data.bom import closest_first_bom, get_bom_climate, bom_obs_types


'''
if you download a single site from http://data.water.vic.gov.au/monitoring.htm
'''

def read_individually_downloaded_sw_file(file_name):
	with open(file_name) as f:
		reader = csv.reader(f)
		rows = [r for r in reader]

	details = rows[13][0]
	# print details
	site_id, site_info, lat, lng, elev = re.match('Site (\d+) (.+) Lat:(.*) Long:(.*) Elev:(.*)', details).groups()
	lat = float(lat)
	lng = float(lng)
	elev = float(elev)

	headers = rows[15]

	date_i = 0; assert headers[date_i] == "Datetime"
	level_i = 1; assert headers[level_i] == "Water Level (m) Mean"
	flow_i = 3; assert headers[flow_i] == "Discharge (Ml/d) Mean"
	old_flow_i = 5; assert headers[old_flow_i] == "Discharge (Ml/d) Mean"

	start_i = 16
	while rows[start_i][level_i] == '':
		start_i += 1

	end_i = len(rows)
	while len(rows[end_i-1]) == 0:
		end_i -= 1

	# print "start_i-end-i", start_i, '-', end_i

	dates = numpy.array([datetime.datetime.strptime(r[date_i], "%d/%m/%Y %H:%M:%S") for r in rows[start_i:end_i]])
	levels = utils.interpolate( numpy.array([utils.as_float(r[level_i]) for r in rows[start_i:end_i]]) )
	flows = utils.interpolate( numpy.array([utils.as_float(r[flow_i]) for r in rows[start_i:end_i]]) )

	return site_id, site_info, lat, lng, elev, dates, levels, flows


'''
if you download a bulk sites from http://data.water.vic.gov.au/monitoring.htm
'''

def read_bulk_downloaded_sw_file(dir_name, site_id, data_types):

	# get details of all sites
	site_details = {}
	with open(os.path.join(dir_name, "Site Details.csv")) as f:
		reader = csv.DictReader(f)
		for row in reader:
			site_details[row["Site Id"]] = row

	data_types_values = []
	for data_type in data_types:
		file_name = os.path.join(dir_name, site_id+"."+data_type+".csv")

		with open(file_name) as f:
			reader = csv.reader(f)
			rows = [r for r in reader]

		headers = rows[2]
		date_i = 0; assert headers[date_i] == "Date"
		data_i = 1; assert headers[data_i] == "Mean"

		start_i = 3

		dates = numpy.array([datetime.datetime.strptime(r[date_i], "%H:%M:%S %d/%m/%Y") for r in rows[start_i:]])
		data = utils.interpolate( numpy.array([utils.as_float(r[data_i]) for r in rows[start_i:]]) )

		data_types_values.append({
			"type": data_type, 
			"dates": dates,
			"data": data
			})


	return site_details[site_id], data_types_values



def test_site():

	file_name = "downloaded_data/data.water.vic/405230_20151022/405230.csv"
	site_id, site_info, lat, lng, elev, dates, levels, flows = read_individually_downloaded_sw_file(file_name)
	print "site_id, site_info, lat, lng, elev", site_id, site_info, lat, lng, elev

	# plt.plot(dates, levels, label="levels")
	# plt.plot(dates, flows/1000, label="flows/1000")
	# plt.legend()
	# plt.show()

	site_id = "405230"
	data_types = ["MeanWaterLevel", "MeanWaterFlow"]
	dir_name = "downloaded_data/data.water.vic/download.20151022110838/"
	site_details, data_types_values = read_bulk_downloaded_sw_file(dir_name, site_id, data_types)

	a_i, b_i = utils.intersection_indices(data_types_values[0]["dates"], dates)
	assert numpy.allclose( data_types_values[0]["data"][a_i], levels[b_i] )

	print site_details
	for d in data_types_values:
		plt.plot(d["dates"], d["data"], label=d["type"])
	plt.legend()
	plt.show()




if __name__ == '__main__':
	# test_site()
	
	bulk_site_dir = "downloaded_data/data.water.vic/download.20151022110838/"
	all_bom_sites_file = 'downloaded_data/stations.txt'
	zipped_sites_dir = 'downloaded_data/bom'

	site_id = "405230"
	data_types = ["MeanWaterLevel", "MeanWaterFlow"]
	site_details, data_types_values = read_bulk_downloaded_sw_file(bulk_site_dir, site_id, data_types)
	dates = data_types_values[1]["dates"]
	flows = data_types_values[1]["data"]

	# TODO could use geofabric AHGFCatchment to find center of catchment 

	lat, lng = (float(site_details["Latitude"]), float(site_details["Longitude"]))
	start = dates[0]
	end = dates[-1]
	print "SITE", lat, lng, start
	closest_names, closest_ids, closest_locations = closest_first_bom(all_bom_sites_file, lat, lng, start)

	for closest_i in range(len(closest_names)):
		climate_data = get_bom_climate(zipped_sites_dir, closest_ids[closest_i])
		# TODO perhaps we could build a continuous timeseries from closer stations
		if '122' in climate_data and \
			'123' in climate_data and \
			climate_data['122']["dates"][0] < start and \
			numpy.abs((climate_data['122']["dates"][-1] - end).days) < 50:

			i_122, i_123 = utils.intersection_indices(climate_data['122']["dates"], climate_data['123']["dates"])
			assert numpy.all(climate_data['122']["dates"][i_122] == climate_data['123']["dates"][i_123])

			closest_temp_dates = climate_data['122']["dates"][i_122]
			closest_temp_data = (climate_data['122']["values"][i_122] + climate_data['123']["values"][i_123])/2.
			
			assert (closest_temp_dates[-1] - closest_temp_dates[0]).days == (len(closest_temp_dates) - 1)
			
			print "closest found temperature", closest_names[closest_i], closest_ids[closest_i], closest_locations[closest_i]
			break			

	for closest_i in range(len(closest_names)):
		climate_data = get_bom_climate(zipped_sites_dir, closest_ids[closest_i])
		if '136' in climate_data:
			closest_rain_dates = climate_data['136']["dates"]
			closest_rain_data = climate_data['136']["values"] 
			print "closest found rainfall", closest_names[closest_i], closest_ids[closest_i], closest_locations[closest_i]
			break



	print bom_obs_types