import os
import json
import numpy
import csv
import datetime
import re
import zipfile
import matplotlib.pylab as plt
import itertools
from fetch_data import utils, bom, vic_water_surface


def save_site(site_id):
	bulk_site_dir = "downloaded_data/data.water.vic/download.20151022110838/"
	all_bom_sites_file = 'downloaded_data/stations.txt'
	zipped_sites_dir = 'downloaded_data/bom'

	# get levels and flows from data.vic.water
	# site_id = "405230"
	data_types = ["MeanWaterLevel", "MeanWaterFlow"]
	site_details, data_types_values = vic_water_surface.read_bulk_downloaded_sw_file(bulk_site_dir, site_id, data_types)
	dates = data_types_values["MeanWaterFlow"]["dates"]
	flows = data_types_values["MeanWaterFlow"]["data"]
	level_dates = data_types_values["MeanWaterLevel"]["dates"]
	levels = data_types_values["MeanWaterLevel"]["data"]
	
	lat, lng = (float(site_details["Latitude"]), float(site_details["Longitude"])) # TODO could use geofabric AHGFCatchment to find center of catchment 
	closest_names, closest_ids, closest_locations = bom.closest_first_bom(all_bom_sites_file, lat, lng, dates[0])

	# get climate from BOM
	closest_rain_i, closest_rain_dates, closest_rain_data = bom.closest_obs('136', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	
	closest_max_temp_i, closest_max_temp_dates, closest_max_temp_data = bom.closest_obs('123', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	
	closest_min_temp_i, closest_min_temp_dates, closest_min_temp_data = bom.closest_obs('122', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	

	# keep intersections
	multi_names = ["flows", "levels", "closest_min_temp", "closest_max_temp", "closest_rain"]
	multi_dates = [dates, level_dates, closest_min_temp_dates, closest_max_temp_dates, closest_rain_dates]
	multi_series = [flows, levels, closest_min_temp_data, closest_max_temp_data, closest_rain_data]
	intersection_i = utils.intersection_indices(multi_dates)
	for i in range(len(multi_dates)):
		multi_dates[i] = multi_dates[i][intersection_i[i]]
		multi_series[i] = multi_series[i][intersection_i[i]]

		assert numpy.all(multi_dates[i] == multi_dates[0])
		assert (multi_dates[i][-1] - multi_dates[i][0]).days == (len(multi_dates[i]) - 1) # check contiguous, TODO: otherwise add nans then interpolate

	print "SITE", lat, lng, dates[[0,-1]]
	print bom.bom_obs_types

	write_data = {
		"site_details": site_details, 
		"closest_details": {
			"closest_rain": { "name": closest_names[closest_rain_i], "id": closest_ids[closest_rain_i], "location": closest_locations[closest_rain_i], },
			"closest_max_temp": { "name": closest_names[closest_max_temp_i], "id": closest_ids[closest_max_temp_i], "location": closest_locations[closest_max_temp_i], },
			"closest_min_temp": { "name": closest_names[closest_min_temp_i], "id": closest_ids[closest_min_temp_i], "location": closest_locations[closest_min_temp_i], },
		},
		"dates" : [d.strftime("%d/%m/%Y %H:%M:%S") for d in multi_dates[0]],
	}
	for i in range(len(multi_dates)):
		write_data[multi_names[i]] = multi_series[i].tolist()

	with open(os.path.join("sw_data/", site_id+'.json'), 'w') as f:
		f.write(json.dumps(write_data))

def save_all_sites():

	# plot_site("405230")
	sites = [
			"405230", # CORNELLA CREEK @ COLBINABBIN			# outflow from eppalock
			"406207", # CAMPASPE RIVER @ EPPALOCK			#	or
			"406225", # CAMPASPE RIVER AT LAKE EPPALOCK (OLET MEAS. WEIR)			#	or 
			"406219", # CAMPASPE RIVER @ LAKE EPPALOCK (HEAD GAUGE)			# next is
			"406201", # CAMPASPE RIVER @ BARNADOWN			# but other creeks enter before then			# possibly 
			"406214", # AXE CREEK @ LONGLEA			# then enters
			"406224", # MOUNT PLEASANT CREEK @ RUNNYMEDE			# then 
			# noflow "406218", # CAMPASPE RIVER @ CAMPASPE WEIR (HEAD GAUGE)			# then
			# noflow "406275", # CAMPASPE RIVER @ BURNEWANG-BONN ROAD			# then at drain
			"406202", # CAMPASPE RIVER @ ROCHESTER D/S WARANGA WESTERN CH SYPHN
			"406764", # CAMPASPE DRAIN NO 5 @ OUTFALL			# nearby drains enter? exit? cross?
			"406766", # CAMPASPE DR NO 4 U/S NORTHERN HIGHWAY
			"406744", # BAMAWM DRAIN NO.3 EXTENSION @ ODONNEL ROAD			# then enters ? 
			"406264", # MILLEWA CREEK @ NORTHERN HIGHWAY ECHUCA			# far enter? exit? irrelevant?
			"406759", # ROCHESTER NO 14 OUTFALL @ COCKBILL ROAD			# then 
			# noflow "406276", # CAMPASPE RIVER @ FEHRINGS LANE
			"406265", # CAMPASPE RIVER @ ECHUCA			# probably also relevant
			"409200", # MURRAY RIVER @ ECHUCA			# etc.			# chanel head
			# nolevel "405705", # WARANGA WESTERN CHANNEL @ 0 MILE 40 CHAIN STRUCTURE			# enters?, crosses? at weir
			"405229", # WANALTA CREEK @ WANALTA			# crosses?
			"405717", #CENTRAL GOULBURN NO 9 CHANNEL @ OFFTAKE
					]

	for site_id in sites:
		save_site(site_id)

	sites_geojson = {"type": "FeatureCollection", "features": [],}
	for site_id in sites:
		with open(os.path.join("sw_data/", site_id+'.json')) as f:
			site_data = json.loads(f.read())
		sites_geojson["features"].append({ 
					"type": "Feature",
					"geometry": {
						"type": "Point",
						"coordinates": [float(site_data["site_details"]["Longitude"]), float(site_data["site_details"]["Latitude"])]
					},
					"properties": site_data["site_details"]
					# {	
					# 	"site": site_id,
					# 	"closest_details": site_data["closest_details"],
					# 	"site_details": 
					# }
				})

	with open("clipped_data/sw_sites.json",'w') as f:
		f.write(json.dumps(sites_geojson))





def plot_site(site_id):
	with open(os.path.join("sw_data/", site_id+'.json')) as f:
		site_data = json.loads(f.read())

	site_details = site_data["site_details"]
	dates = [datetime.datetime.strptime(d, "%d/%m/%Y %H:%M:%S") for d in site_data["dates"]]

	for k in ["flows", "levels", "closest_min_temp", "closest_max_temp", "closest_rain"]:
		plt.plot(dates, site_data[k], label=k)
	plt.legend()
	plt.show()

def alphabeta_to_vtau(alpha, beta):

	v = [ beta[i]/(1.+ alpha[i]) for i in range(len(alpha)) ]

	tau = [ -1. / numpy.log(-1.*a) for a in alpha ]

	return v, tau

def ab_to_alphabeta(a,b):

	# TODO check for complex or no poles
	beta = numpy.roots(a)

	# TODO generalize for 3 or more stores
	size = 2
	M = numpy.empty((size,size))
	M[0,:] = 1.
	M[1,:] = beta
	alpha = numpy.linalg.solve(M, b)

	return alpha, beta[::-1]

def arma(a, b, q, u, k):
	# a[0] = a_2 .. , b[0]= b_1 ..
	# q_k = (a[0]*q[k-1]) + b[0]*u[k]
	q_k = (a[0]*q[k-1] + a[1]*q[k-2]) + b[0]*u[k] + b[1]*u[k-1]

	# q_k = -1.*numpy.sum([a[i]*q[k-i] for i in range(1,len(a))]) + numpy.sum([b[i]*u[k-i] for i in range(len(b))])
	return q_k

def cmd(
		M_k_m_1, # 100
		P_k,
		T_k, 
		d, # 200
		e, # 0.166
		f, # ? 0.5-1.3 
	):
	'''
	ET[k] , M[k] and T[k] are the ET, CMD and temperature for timestep k, 
	c_1 and c_2 are parameters
	u[k] effective rainfall 
	 
	P[k] is the rainfall depth for timestep k and 
	c_3 and c_4 are parameters
	For M[k] < 0, u[k] is
	increased by M k and M k set to zero


		M[k-1] = 100 # 100
		P[k] = [1,2,3,4]
		T[k] = [1,2,3,4]
		d = 200 # 200
		e = 0.166 # 0.166
		f = 1. # ? 0.5-1.3
	'''
	
	"""
	"A catchment moisture deficit module for the IHACRES rainfall-runoff model"
	and 
	"Corrigendum"
	"""
	if M_k_m_1 < d:
		M_k = M_k_m_1 * numpy.exp(-1. * P_k / d)
	elif M_k_m_1 < d + P_k: # and d <= M_k_m_1 
		M_k = d * numpy.exp(-1.*(P_k - M_k_m_1 + d)/d)
	else: # d + P_k <= M_k_m_1
		M_k = M_k_m_1 - P_k

	"""
	(1) of "Evaluation of streamflow predictions by the IHACRES rainfall-runoff model in two South African catchments"
	"""
	f = f * d

	if T_k < 0:
		E_k = 0
	elif M_k < f: # and 0 < T_k
		E_k = e * T_k
	else: #  f <= M_k and 0 < T_k
		E_k = e * T_k * numpy.exp(2. * (1. - M_k/f))

	M_k = M_k + E_k

	U_k = P_k + M_k - M_k_m_1

	return U_k, M_k, E_k

def cmd_ihacres(		
		M_k_m_1, 
		P_k,
		T_k,
		c,
		tau,
		T_ref
		):

	rs_k = P_k * (T_ref - T_k) / T_ref

	M_k = M_k_m_1 + (rs_k - M_k_m_1) / tau

	U_k = c * rs_k * M_k

	return U_k, M_k

	# U_k, M_k = cmd_ihacres(		
	# 	M_k_m_1 =  M_k, 
	# 	P_k = rain[k],
	# 	T_k = mean_temp[k],
	# 	c = .5,
	# 	tau = 82,
	# 	T_ref = 1.1*numpy.max(mean_temp)
	# 	)


def tau_v_to_ab(tau, v):

	alpha = [numpy.exp(-1. / tau_i) for tau_i in tau]
	beta = [v[i] * (1. - alpha[i]) for i in range(len(v))]

	# https://github.com/josephguillaume/hydromad/blob/ebd858632e3431ac4bb236ea0dd5b51a4927a335/R/tfUtils.R#L380	
	# a = [1.]
	# for i in range(len(alpha)):
	# 	sum_prod = (-1.)**i * numpy.sum( map(numpy.prod,itertools.combinations(alpha, i+1)) )
	# 	a.append( sum_prod )

	assert len(alpha) == 1 or len(alpha) == 2  #or len(alpha) == 3

	if len(alpha) == 1:
		a = [alpha[0]]
		b = [beta[0]]
	else: #len(alpha) == 2:
		a = [(alpha[0] + alpha[1]),
			-1*(alpha[0] * alpha[1])]

		b =	[beta[0] + beta[1],
			-1.*(beta[0] * (alpha[1]) +
			beta[1] * (alpha[0]))]	

	# else: # len(alpha) == 3:
	# 	a = [1.,
	# 		alpha[0] + alpha[1] + alpha[2],
	# 		-1.*(alpha[0] * alpha[1] +
	# 		alpha[0] * alpha[2] +
	# 		alpha[1] * alpha[2]),
	# 		alpha[0] * alpha[1] * alpha[2]]

	# 	## all stores in parallel
	# 	b =	[beta[0] + beta[1] + beta[2],
	# 		-1.*(beta[0] * (alpha[1] + alpha[2]) +
	# 		beta[1] * (alpha[0] + alpha[2]) +
	# 		beta[2] * (alpha[0] + alpha[1])),
	# 		(beta[0] * alpha[1] * alpha[2] +
	# 		beta[1] * alpha[0] * alpha[2] +
	# 		beta[2] * alpha[0] * alpha[1])]

	return a, b

def run(x):

	"""
	effective rainfall (using CMD model)
	"""
	M_k = 100.
	U = []
	M = []
	E = []
	for k in range(len(dates)):
		U_k, M_k, E_k = cmd(
					M_k_m_1 = M_k, # 100
					P_k = rain[k],
					T_k = mean_temp[k], 
					# d = 200,
					# e = 0.166,
					# f = 0.9
					d = x[0], # 200
					e = x[1], # 0.166
					f = x[2], # ? 0.5-1.3
				)
		U.append(U_k)
		M.append(M_k)
		E.append(E_k)

	"""
	flow (using IHACRES)
	"""
	a, b = tau_v_to_ab( tau = x[3:5], v = [x[5], x[6]*(1.-x[2])])
	# a, b = tau_v_to_ab( tau = [x[3]], v = [x[4]])
	
	print "a, b", a, b


	Q = [ 1., 1.]
	for k in range(2, len(dates)):
		Q_k = arma(a, b, Q, U, k)
		Q.append(Q_k)

	return U,M,E,Q

def objective(x):
	U,M,E,Q = run(x)
	return numpy.sum((flows-Q)**2)/obj_denominator
	# return 1. - numpy.sum((flows-Q)**2)/obj_denominator
	# return numpy.linalg.norm(Q - flows, ord=2)

	# plt.plot(Q) 
	# plt.plot(flows, '--')
	# plt.show()




if __name__ == '__main__':
	# save_site("405230")
	# plot_site("406219")
	# save_all_sites()

	site_id = "405230"
	with open(os.path.join("sw_data/", site_id+'.json')) as f:
		site_data = json.loads(f.read())

	site_details = site_data["site_details"]
	dates = numpy.array([datetime.datetime.strptime(d, "%d/%m/%Y %H:%M:%S") for d in site_data["dates"]])
	flows = numpy.array(site_data["flows"])
	catchments_area = 1e6 * float(site_details['Drainage Area (Sq.km)'])
	rain = numpy.array(site_data["closest_rain"]) * catchments_area
	mean_temp = (numpy.array(site_data["closest_max_temp"]) + numpy.array(site_data["closest_min_temp"])) / 2.
	max_temp = numpy.array(site_data["closest_max_temp"])
	obj_denominator = numpy.sum((flows-numpy.mean(flows))**2) 

	# 1000 m3 = 1 Ml


	from scipy import optimize
	# x_0 = [-1.7836, 0.7859, 20.4317, 19.9046, 200, 0.166, 0.9]
	# x_0 = [-1.7836, 0.7859, 20.4317, 19.9046]
	x_0 = [200, 0.166, 0.9, 1.1, 30., 0.5, 0.5]
	# x_0 = [1.1, 30., 0.5, 0.5]
	# x_0 = [1.1, 0.5]
	# TODO ensure sum(vs) = 0
	res = optimize.minimize(fun=objective, 
								x0 = x_0,
								# method = 'CG',
								method = 'L-BFGS-B', 
								# bounds = [(2., 3.), (0., 1.)]
								bounds = [(150., 350.), (0.1, 0.2), (0.5,1.3),
										(0.1, 2.), (10.,200.), (0., 1.), (0., 1.)]
								)
	print res

	U,M,E,Q = run(res.x)
	plt.plot(Q, label='mod Q')
	# plt.plot(rain, label='rain')
	# plt.plot(max_temp, label='max_temp')
	# plt.plot(U, label='mod U')
	plt.plot(flows, '--', label='obs flow')
	plt.legend()
	plt.show()



	print "objective", objective(res.x)


	# import statsmodels.tsa.api as tsa
	# arma =tsa.ARMA(flows, order=(2,2), exog=U)
	# results= arma.fit()
	# print results.predict(30, 40, exog=U)


