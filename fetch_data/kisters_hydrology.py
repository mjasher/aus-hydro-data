import csv
import json
import urllib2
import math
import os
import numpy

"""
========================================================
Scrape surface and ground water data from Kister's API
	eg. Vic. http://data.water.vic.gov.au/monitoring.htm
		NSW http://realtimedata.water.nsw.gov.au/water.stm
		Qld https://www.dnrm.qld.gov.au/water/water-monitoring-and-data/portal
	Note: 
		API URLS will differ slightly from above

michael.james.asher@gmail.com
October 2015
========================================================
"""


# http://kisters.com.au/doco/hydllp.htm
# see WIR user guide 
# http://webcache.googleusercontent.com/search?q=cache:zczMmAj4stUJ:kisters.com.au/doco/hydllp.htm+&cd=2&hl=en&ct=clnk&gl=au&client=ubuntu
# Dates take the form yyyymm22hhiiee


# fetch bores/gauges in bounding box
# ----------------------------------
def fetch_sites(url, bounding_box, file_name):
	parameters = {
		"params":{
			"return_type": "array",
			# "sitelist_filter": "FILTER(TSFILES(PROV),MATCH(210*))", 
			# "geo_filter":{"circle":["'+latitude+'","'+longitude+'","'+radiusdegree+'"]}, 
			"geo_filter":{"rectangle": bounding_box}, 
			# "field_list": ["station","stname","shortname","latitude","longitude","elev"],
			"table_name":"site"
		},
		"function": "get_db_info",
		"version": 2
	}

	params = "jsoncallback=printData&" + json.dumps(parameters)

	params = params.replace(' ','')
	print "fetch_sites params", params

	response = urllib2.urlopen(url+params).read()

	response = json.loads( response.replace('printData(','')[:-2] ) #");"

	with open(file_name, 'w') as file:
		file.write(json.dumps(response))


# ----------------------------------
def write_sites_geojson(response_file, name):
	geojson = {"type": "FeatureCollection", "features": []}
	
	with open(response_file) as file:
		response = json.loads(file.read())

	for row in response['_return']['rows']:
		geojson["features"].append({ 
				"type": "Feature",
				"geometry": {
					"type": "Point",
					"coordinates": [float(row["longitude"]), float(row["latitude"])]
				},
				"properties": row
			})

	with open(name, 'w') as bores:
		bores.write(json.dumps(geojson))

# ----------------------------------
def get_datasources_by_site(url, site_list):

	parameters = {
		"params":{
			"site_list": ','.join(site_list),
		},
		"function": "get_datasources_by_site",
		"version": 1
	}

	params = json.dumps(parameters).replace(' ','')
	print "get_datasources_by_site params", params

	response = urllib2.urlopen(url+params).read()
	print "get_datasources_by_site response", response
	# return json.loads( response.replace('printData(','')[:-2] )
	return json.loads( response )

# ----------------------------------
def get_variable_list(url, site_list, datasource):

	parameters = {
		"params":{
			"site_list": ','.join(site_list),
			"datasource": datasource
		},
		"function": "get_variable_list",
		"version": 1
	}

	params = json.dumps(parameters).replace(' ','')
	print "get_variable_list params", params

	try:
		response = urllib2.urlopen(url+params).read()
		response = json.loads( response )
		# return json.loads( response.replace('printData(','')[:-2] )
	except(e):
		print("ERROR", url+params)
		response = {"return":{"sites":[]}}
	
	return response


# for each site, get details of all available time series
#-------------------------------------
# TODO check this get's them all (buffer is not exceeded)
def get_site_variables(url, variable_by_sites_file, sites_file):
	with open(sites_file) as file:
		sites = json.loads(file.read())["_return"]["rows"]

	variable_by_site = {}

	for i in range(int(math.ceil(len(sites)/150.))):
		print "get_site_variables", i*150, '-', (i+1)*150
		datasources_by_site = get_datasources_by_site(url, [ s["station"] for s in sites[i*150:(i+1)*150] ])
		for site in datasources_by_site["return"]["sites"]:
			variable_by_site[site["site"]] = []
			for datasource in site["datasources"]:
				site_variables = get_variable_list(url, [site["site"]], datasource)["return"]["sites"][0]
				for variable in site_variables["variables"]:
					variable["datasource"] = datasource
					variable_by_site[site["site"]].append(variable)
					# print site_variables["site_details"]["name"], variable['name']
				assert(site["site"] == site_variables["site"])
				# print "site", site, "datasource", datasource, get_variable_list([site["site"]], datasource)
	
	with open(variable_by_sites_file,'w') as f:
		f.write( json.dumps(variable_by_site) )


# generic call to json API
#-------------------------------------
# todo wrap everything in this
def generic_call(url, parameters):
	params = json.dumps(parameters).replace(' ','')
	print url+params
	response = urllib2.urlopen(url+params).read()
	# print response
	# return  json.loads( response.replace('printData(','')[:-2] )
	return  json.loads( response )


# for each site, get all timeseries
#-------------------------------------
# takes a long time [Finished in 444.7s]
def get_all_ts(url, variable_by_site_file, all_ts_directory):

	with open(variable_by_site_file) as f:
		variable_by_site = json.loads(f.read())

	by_site = {}
	for site in variable_by_site:
		tss = []
		for variable in variable_by_site[site]:
			ts =  generic_call(url, {
				"params":{
					"site_list": site,
					"interval": "day",
					# "datasource": "A", #"CP"
					"datasource": variable['datasource'],
					"start_time": variable['period_start'],
					"end_time": variable['period_end'],
					"varfrom": variable['variable'],
					"varto": variable['variable'],
					"data_type":"mean",
					"multiplier":"1"
				},
				"function": "get_ts_traces",
				"version": 2
			})
			tss.append(ts)

		by_site[site] = tss
		if len(by_site[site]) > 0:
			with open(os.path.join(all_ts_directory, site+".json"),'w') as f:
				f.write( json.dumps(by_site[site]) )

	# return by_site	

# write an object {"varible type" : "geojson of sites with link to csv" }
def find_sites_with_data(sites_file, variable_by_sites_file, all_ts_directory, destination_dir):
	
	with open(sites_file) as file:
		sites = json.loads(file.read())["_return"]["rows"]

	with open(variable_by_sites_file) as file:
		variable_by_sites = json.loads(file.read())

	site_files = [f.replace('.json','') for f in os.listdir(all_ts_directory)]

	sites_geojson = {"type": "FeatureCollection", "features": [], "properties": {"variables": {}}}

	for site in sites:
		site_code = site["station"]
		# if site has data
		if site_code in site_files:

			site_vars = []

			for var in variable_by_sites[site["station"]]:
				variable_code = var["variable"]

				# shouldn't matter that this overwrites
				sites_geojson["properties"]["variables"][variable_code] = {
									"name": var["name"],
							        "units": var["units"],
							        "datasource": var["datasource"],
							        "subdesc": var["subdesc"],
							        "variable": var["variable"],
									}

				site_var_csv = os.path.join(destination_dir, 'kisters_ts', 
										site_code  + '_' + variable_code + '.csv')

				site_vars.append({
					"file": site_var_csv,
					"code": variable_code
					})

				# write csv with timeseries	for chosen site and variable	
				# ------------------------------------------------------		
				with open(os.path.join(all_ts_directory, site_code +'.json')) as f:
					site_ts = json.loads(f.read())

				site_var_trace = filter(lambda s: s["return"]["traces"][0]["varto_details"]["variable"] == variable_code, 
									site_ts)
				
				# TODO check that all site_var_trace are truncated versions of one another
				longest_i = numpy.argmax( [len(s["return"]["traces"][0]["trace"]) for s in site_var_trace] )
				chosen_site_var = site_var_trace[longest_i]
			
				assert len(chosen_site_var["return"]["traces"]) == 1

				heading = ["Time", "Value", "Quality"]
				ts_rows = [[row["t"], row["v"], row["q"]] for row in chosen_site_var["return"]["traces"][0]["trace"] ]
				details = chosen_site_var["return"]["traces"][0]["varto_details"]

				with open(site_var_csv, 'w') as f:
					writer = csv.writer(f)
					writer.writerow(heading)
					writer.writerows(ts_rows)
				# ------------------------------------------------------		

			site_data = site.copy()
			site_data.update({ "variables": site_vars })
			sites_geojson["features"].append({ 
						"type": "Feature",
						"geometry": {
							"type": "Point",
							"coordinates": [float(site["longitude"]), float(site["latitude"])]
						},
						"properties": site_data
					})

	print len(sites)
	print len(site_files)

	with open(os.path.join(destination_dir, 'kisters_sites_with_data.json'), 'w') as f:
		f.write(json.dumps(sites_geojson))


def run(bounding_box, destination_dir):
	# see http://data.water.vic.gov.au/monitoring.htm
	url = "http://data.water.vic.gov.au/cgi/webservice.server.pl?"
	sites_file = os.path.join(destination_dir, "sites.json")
	variable_by_sites_file = os.path.join(destination_dir, "variable_by_sites.json")
	all_ts_directory = os.path.join(destination_dir, "kisters_sites")

	# download all sites within bounding box
	#-------------------------------------
	# fetch_sites(url, bounding_box, sites_file)

	# write to geojson
	#-------------------------------------
	# write_sites_geojson(sites_file, os.path.join(destination_dir, "sites.geo.json"))

	# for each site, get details of all available time series
	#-------------------------------------
	# get_site_variables(url, variable_by_sites_file, sites_file)

	# for each site, download all timeseries
	#-------------------------------------
	# get_all_ts(url, variable_by_sites_file, all_ts_directory)
	
	# only sites with timeseries
	#-------------------------------------
	find_sites_with_data(sites_file, variable_by_sites_file, all_ts_directory, 
						destination_dir)

if __name__ == '__main__':
	bounding_box = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	destination_dir = "../clipped_data"
	run(bounding_box, destination_dir)