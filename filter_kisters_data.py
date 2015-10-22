import os
import json
import numpy
import csv
import datetime
import urllib2

data_dir = 'clipped_data/'

'''

busted, for example 406219 CAMPASPE RIVER @ LAKE EPPALOCK (HEAD GAUGE) has 141.00 but API doesn't work for it

'''

def filter_kisters_sites(var_of_interest):	
	with open(os.path.join(data_dir, "kisters_sites_with_data.json")) as f:
		kisters_sites = json.loads(f.read())

	# prints all variables for info
	if False:
		all_vars = {}	
		for feat in kisters_sites["features"]:
			for v in feat["properties"]["variables"]:
				if not v["code"] in all_vars:
					variable_info = kisters_sites["properties"]["variables"][v["code"]]
					all_vars[v["code"]] = variable_info["name"] + variable_info["subdesc"]
					try:
						print v["code"], variable_info
					except:
						print v["code"]


	def has_var(feat, var_of_interest):
		if feat["properties"]["active"]:
			for v in feat["properties"]["variables"]:
				if v["code"] == var_of_interest:

					with open(os.path.join('clipped_data', v["file"])) as f:
						rows = [r for r in csv.DictReader(f)]
					values = [float(r["Value"]) for r in rows]
					dates = [r["Time"] for r in rows] 
					parsed_dates = [datetime.datetime.strptime(r["Time"], "%Y%m%d%H%M%S") for r in rows]
					feat["properties"]["file_of_interest"] = v["file"]
					feat["properties"]["start-end"] = str(numpy.min(parsed_dates).year) + "-" + str(numpy.max(parsed_dates).year)

					return True
		return False

	kisters_sites["features"] = filter(lambda f: has_var(f, var_of_interest),  kisters_sites["features"])

	with open(os.path.join(data_dir, "kisters_sites_"+var_of_interest+".json"), 'w') as f:
		f.write(json.dumps(kisters_sites))


def generic_call(url, parameters):
	params = json.dumps(parameters).replace(' ','')
	print url+params
	response = urllib2.urlopen(url+params).read()
	# print response
	# return  json.loads( response.replace('printData(','')[:-2] )
	return  json.loads( response )

def download_site_data():

	url = "http://data.water.vic.gov.au/cgi/webservice.server.pl?"

	# 141.00	A	Discharge (Ml/d)	14/05/1986	31/08/2015	10700	Instantaneous value	18478.4	20/09/1993	0	14/05/1986

	site = "406219"
	variable = {
		"variable": "141.00",
		"datasource": "A",
		# "period_start": "177000101000000",
		# 20150901000000
		"period_start": datetime.datetime.strptime("14/05/1986", "%d/%m/%Y").strftime("%Y%m%d%H%M%S"),
		# "period_end": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
		"period_end": datetime.datetime.strptime("31/08/2015", "%d/%m/%Y").strftime("%Y%m%d%H%M%S"),
	}

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

	with open('temp.json', 'w') as f:
		f.write(json.dumps(ts))



if __name__ == '__main__':
	# for var_of_interest in ["100.00", "141.00"]:
	# 	filter_kisters_sites(var_of_interest)

	download_site_data()