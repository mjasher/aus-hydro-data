
import os
import urllib2
import json

# ================================
#	fetch elevation data from Google Maps API
# ================================

# mapbox_token = '&access_token=pk.eyJ1IjoibWphc2hlciIsImEiOiJTZDBtVVEwIn0.HBpUK8wlBtY-udXQ2bRq_Q'
# elevation_url = 'https://api.tiles.mapbox.com/v4/surface/mapbox.mapbox-terrain-v1.json?layer=contour&fields=ele&points='
# url = elevation_url + point_string + mapbox_token # point_string += p["Longitude"] + "," + p["Latitude"] + ";"
elevation_url = "https://maps.googleapis.com/maps/api/elevation/json?key=AIzaSyCdFirYrzvWJN3rEQp6J_aqi9JxWUTNQuo&locations="
def get_elevation(points):
	point_string = "|".join([str(p["lat"]) + "," + str(p["lng"]) for p in points])
	url = elevation_url + point_string 
	print "---------------------------------"
	data = urllib2.urlopen(url).read()
	return json.loads(data)


def get_elevations(rows, destination_dir):
	all_results = []
	for i in range(1+len(rows)/50):
		results = get_elevation(rows[(i)*50:(i+1)*50])['results']
		for r in results:
			all_results.append(r)

		# with open("elevation/elevations"+str(i)+".json", "w") as f:
		# 		f.write(json.dumps(all_results))

	sites_geojson = {"type": "FeatureCollection", "features": []}
	for i, r in enumerate(all_results):
		assert rows[i]["lat"] == r["location"]["lat"]
		assert rows[i]["lng"] == r["location"]["lng"]
		sites_geojson["features"].append({ 
						"type": "Feature",
						"geometry": {
							"type": "Point",
							"coordinates": [r["location"]["lng"], r["location"]["lat"]]
						},
						"properties": {	
							"elevation": r["elevation"],
							"resolution": r["resolution"],
							"values": rows[i]["values"],
							"dates": rows[i]["dates"],
							"station": rows[i]["station"],
							"bore level below": rows[i]["bore level below"]
						}
					})	

	with open(os.path.join(destination_dir, "bore_elevations.json"), "w") as f:
		f.write(json.dumps(sites_geojson))
	with open(os.path.join(destination_dir,"../clipped_data/", "bore_elevations.json"), "w") as f:
		f.write(json.dumps(sites_geojson))
	return all_results


