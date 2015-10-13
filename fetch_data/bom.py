from lxml import html
import urllib
import urllib2
import re
import os
import csv
import json
import zipfile

"""
========================================================
Scrape BOM observations in a given area


michael.james.asher@gmail.com
October 2015
========================================================
"""

bom_obs_types = {
 '136': 'Rainfall amount (millimetres)',
 '123': 'Minimum temperature (Degree C)',
 '122': 'Maximum temperature (Degree C)',
 '193': 'Daily global solar exposure (MJ/m*m)'
}


"""
Get all BOM sites in a bounding box
	* list of sites [manually]( http://www.bom.gov.au/climate/data ) or
 	* ftp://ftp.bom.gov.au/anon2/home/ncc/metadata/sitelists/stations.zip -> stations.txt
"""
def list_sites(file_name, bounding_box):
	site_ids = []
	site_locations = []
	with open(file_name) as f:
		rows = [r for r in f]
		for row in rows[4:-8]:
			site_id = row[0:8].strip()
			lat = float(row[71:80])
			lon = float(row[80:90])
			if bounding_box[1][0] <= lat and lat <= bounding_box[0][0] and bounding_box[0][1] <= lon and lon <= bounding_box[1][1]:
				site_ids.append(site_id)
				site_locations.append({"lat": lat, "lon": lon})

	return site_ids, site_locations

"""
For each site, download available timeseries
"""
def download_bom_sites(site_ids, destination_dir):
	print("download_bom_sites will take a long time for many sites")
	base_url = "http://www.bom.gov.au"
	obs_codes = bom_obs_types.keys()
	# obs_codes = ['136', '123', '122', '193'] # daily rainfall, daily min temperature, daily max temperature, solar exposure
	
	for site_id in site_ids:
		for obs_code in obs_codes:
			url = base_url + "/jsp/ncc/cdio/weatherData/av?p_nccObsCode="+obs_code+"&p_display_type=dailyDataFile&p_stn_num="+site_id+"&p_startYear="
			response = urllib2.urlopen(url).read()
			tree = html.fromstring(response)
			try: 
				href = tree.xpath('//*[@id="content-block"]/ul[2]/li[2]/a')[0].attrib["href"]
				urllib.urlretrieve(base_url+href, os.path.join(destination_dir, 'bom', site_id + "_" + obs_code + ".zip"))
			except:
				print obs_code, site_id, "not working"
				print url



# daily rainfall, daily min temperature, daily max temperature, solar exposure

def is_float(string):
	try:
		a = float(string)
		return True
	except:
		return False

"""
Combine downloaded timeseries into geojson
"""
def bom_ts_to_geojson(site_ids, site_locations, zipped_sites_dir, destination_dir):

	bom_re = re.compile('(\d{6})_(\d{3}).zip')

	zipped_files = [f for f in os.listdir(zipped_sites_dir) if bom_re.match(f)]

	sites_geojson = {"type": "FeatureCollection", "features": [], "properties":{ "variables": bom_obs_types}}
	
	# data_by_type = {k:  for k in bom_obs_types.values()}

	site_vars = {}

	for zipped_f in zipped_files:
		site_id = bom_re.match(zipped_f).group(1)
		obs_code = bom_re.match(zipped_f).group(2)
		obs_type = bom_obs_types[obs_code]

		archive = zipfile.ZipFile(os.path.join(zipped_sites_dir, zipped_f))
		csvfile = filter(lambda filename: filename.endswith(".csv"), archive.namelist())[0]
		reader = csv.DictReader(archive.open(csvfile))

		raw_rows = [row	for row in reader if is_float(row[obs_type])]
		# dates = [row["Year"]+"-"+row["Month"]+"-"+row["Day"] for row in raw_rows]
		# values = [float(row[obs_type]) for row in raw_rows]

		dest_csv = os.path.join(destination_dir, 'bom_ts', csvfile)
		with open(dest_csv, 'w') as f:
			writer = csv.writer(f)
			writer.writerow(["Year", "Month", "Day", obs_type])
			writer.writerows([[row["Year"], row["Month"], row["Day"], float(row[obs_type])] for row in raw_rows])

		if not site_id in site_vars:
			site_vars[site_id] = []

		site_vars[site_id].append({
				"file": dest_csv,
				"code": obs_code
			})

	for site_id in site_vars.keys():
		location = site_locations[site_ids.index(site_id)]
		sites_geojson["features"].append({ 
					"type": "Feature",
					"geometry": {
						"type": "Point",
						"coordinates": [location["lon"], location["lat"]]
					},
					"properties": {	
						"site": site_id,
						"variables": site_vars[site_id]
					}
				})

	with open(os.path.join(destination_dir, 'bom_sites_with_data.json'), 'w') as f:
		f.write(json.dumps(sites_geojson))



def run(bounding_box, destination_dir):
	
	site_ids, site_locations = list_sites('../downloaded_data/stations.txt', bounding_box)
	
	print len(site_ids), "sites"

	# download_bom_sites(site_ids, 'downloaded_data')
	
	zipped_sites_dir = '../downloaded_data/bom'
	
	bom_ts_to_geojson(site_ids, site_locations, zipped_sites_dir, destination_dir)


if __name__ == '__main__':
	bounding_box = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	destination_dir = "../clipped_data"
	run(bounding_box, destination_dir)


'''
NOTES

climate averages eg.
http://www.bom.gov.au/clim_data/cdio/tables/text/IDCJCM0037_066196.csv

climate data eg.
http://www.bom.gov.au/jsp/ncc/cdio/weatherData/av?p_nccObsCode=136&p_display_type=dailyDataFile&p_stn_num=080015&p_startYear=

Find zip download: 
$(".downloads li a")[1].href
//*[@id="content-block"]/ul[2]/li[2]/a

'''