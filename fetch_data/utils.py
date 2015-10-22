import numpy
'''
use like interpolate( numpy.array([as_float(r[level_i]) for r in rows]) )
'''
def as_float(string):
	try:
		f = numpy.float(string)
		return f
	except:
		return numpy.nan

def interpolate(array):
	new_array = array.copy()
	def where_true(a):
		return a.nonzero()[0]
	nans = numpy.isnan(new_array)
	new_array[nans]= numpy.interp(where_true(nans), where_true(~nans), new_array[~nans])
	return new_array


'''
	some and others must be sorted !!!
'''
# def intersection_indices(some, others):
# 	shared = set(some).intersection(set(others))
# 	some_i = [i for i in range(len(some)) if some[i] in shared]
# 	others_i = [i for i in range(len(others)) if others[i] in shared]

# 	return some_i, others_i

	# print list(set(data_types_values[0]["dates"]).intersection(dates))[:20]

'''
	each series in multiple_series must be sorted !!!
'''
def intersection_indices(multiple_series):
	shared = set.intersection(*[set(series) for series in multiple_series])
	shared_i = []
	for series in multiple_series:
		shared_i.append([i for i in range(len(series)) if series[i] in shared])
	return shared_i