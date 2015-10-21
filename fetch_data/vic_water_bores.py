import csv
import json
import os
import numpy
import datetime
import matplotlib.pylab as plt

"""
========================================================
You can download surface and ground water data from Kister's API using kisters_hydrology.py
However many bores seem to be missing. This file uses the downloaded csv from 
http://data.water.vic.gov.au/monitoring.htm
--> Data Extracts
--> Groundwater Data
--> Water levels
(http://data.water.vic.gov.au/wgen/state/GW level data.zip)
Columns
	BORE_ID
	DATE 
	METHOD
	CONDITION
	QUALITY
	WLMP_(m)
	DBNS_(m)  Depth below natural surface
	RWL_mAHD The Australian Height Datum is a geodetic datum for altitude measurement in Australia. It is the mean sea level for 1966-1968 and is assigned the value of zero.


michael.james.asher@gmail.com
October 2015
========================================================
"""

important_bores = {
	"82999": "Barnadown zone, Coliban Basalt, Shepparton Formation sands, stable",
	#
	"89580": "Elmore-Rochester zone, Shepparton Fm sands, 38.48-50m, well connected",
	"89574": "Elmore-Rochester zone, Deep Lead, 84-88m",
	#
	"47254": "Bamawm zone, Shepparton Fm sands/clays, 25-26m, poorly connected north of Waranga Western Channel",
	"47253": "Bamawm zone, Deep Lead, 123-129m",
	#
	"79329": "Echucha zone, Shepparton Fm sands/clays?, 6m",
	"79324": "Echucha zone, Deep Lead?, 78-84m, AND for seasonal allocations of Elmore-Rochester, Bamawm and Euchuca zones",
	#
	"62589": "for seasonal allocations of Barnadown zone",
}

level_file = "../downloaded_data/GW level data.csv"
site_file = "../downloaded_data/GW site data.csv"
dest_dir = "../clipped_data/"

def load_sites():
	locations = {k: {} for k in important_bores}
	with open(site_file) as f:
		reader = csv.DictReader(f)
		for row in reader:
			if row["STATION"].strip() in locations:
				locations[row["STATION"].strip()]["lat"] = float(row["LATITUDE"])
				locations[row["STATION"].strip()]["lng"] = float(row["LONGITUDE"])
		print row.keys()

	print locations
	return locations


def load_level():
	important_data = {k: [] for k in important_bores}
	locations = load_sites()
	geojson = {"type": "FeatureCollection", "features": []}

	with open(level_file) as f:
		reader = csv.reader(f)
		rows = [r for r in reader]

	for row in rows:
		BORE_ID, DATE, METHOD, unsure, CONDITION, QUALITY, WLMP_m, DBNS_m, RWL_mAHD = row
		if BORE_ID.strip() in important_data:
			important_data[BORE_ID.strip()].append([DATE, DBNS_m, RWL_mAHD])

	keys = important_data.keys()
	for i, k in enumerate(keys):
		date = numpy.array([datetime.datetime.strptime(r[0].strip(), "%m/%d/%Y") for r in important_data[k]])
		DBNS_m = numpy.array([float(r[1]) for r in important_data[k]])
		RWL_mAHD = numpy.array([float(r[2]) for r in important_data[k]])
		sort_i = numpy.argsort(date)

		geojson["features"].append({ 
				"type": "Feature",
				"geometry": {
					"type": "Point",
					"coordinates": [locations[k]["lng"], locations[k]["lat"]]
				},
				"properties": {
					"station": k,
					"info": important_bores[k],
					"date": [d.strftime("%Y%m%d%H%M%S") for d in date[sort_i]],
					"DBNS_m": DBNS_m[sort_i].tolist(),
					"RWL_mAHD": RWL_mAHD[sort_i].tolist(),
				}
			})

		plt.subplot(numpy.ceil(len(keys)/2.), 2, i+1)
		plt.plot(date[sort_i],RWL_mAHD[sort_i])
		plt.title(k + important_bores[k])

	plt.show()

	with open(os.path.join(dest_dir, "vic_water_bores.json"), 'w') as f:
		f.write(json.dumps(geojson))

if __name__ == '__main__':

	load_level()
