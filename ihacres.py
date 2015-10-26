
import numpy

def cmd():
	'''
	
	ET[k] , M[k] and T[k] are the ET, CMD and temperature for timestep k, 
	c_1 and c_2 are parameters
	u[k] effective rainfall 
	 
	P[k] is the rainfall depth for timestep k and 
	c_3 and c_4 are parameters
	For M[k] < 0, u[k] is
	increased by M k and M k set to zero

	'''

	M[k-1] = 100 # 100
	P[k] = [1,2,3,4]
	T[k] = [1,2,3,4]
	d = 200 # 200
	e = 0.166 # 0.166
	f = 1. # ? 0.5-1.3
	
	"""
	"A catchment moisture deficit module for the IHACRES rainfall-runoff model"
	and 
	"Corrigendum"
	"""
	if M[k-1] < d:
		M[k] = M[k-1] * numpy.exp(-1. * P[k] / d)
	elif M[k-1] < d + P[k]: # and d <= M[k-1] 
		M[k] = d * numpy.exp(-1.*(P[k] - M[k-1] + d)/d)
	else: # d + P[k] <= M[k-1]
		M[k] = M[k-1] - P[k]

	"""
	(1) of "Evaluation of streamflow predictions by the IHACRES rainfall-runoff model in two South African catchments"
	"""
	if T[k] < 0:
		E[k] = 0
	elif M[k] < f: # and 0 < T[k]
		E[k] = e * T[k]
	else: #  f <= M[k] and 0 < T[k]
		E[k] = e * T[k] * numpy.exp(2. * (1. - M[k]/f))

	M[k] = M[k] + E[k]

	U[k] = P[k] + M[k] - M[k-1]

	return U, M


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


def test_ab_to_alphabeta():
	'''
	(10) from "Computation of the instantaneous unit hydrograph and identifiable component flow with application to two small upload catchment"

	q[k] = -1.*(a[0]*q[k-1] + a[1]*q[k-2]) + b[0]*u[k] + b[1]*u[k-1]
	1.*q[k] + a[0]*q[k-1] + a[1]*q[k-2] = b[0]*u[k] + b[1]*u[k-1]
	(1. + a[0]z + a[1]z^2) * q[k] = (b[0] + b[1]z) * u[k]
	q[k] = ( (b[0] + b[1]z) / (1. + a[0]z + a[1]z^2) ) * u[k]

	b0 = alpha0 + alpha1
	b1 = alpha0*beta1 + alpha1*beta0

	b0 = alpha0 + alpha1 + alpha3
	b1 = alpha0*(beta1+beta2) + alpha1*(beta0+beta2) + alpha2*(beta0+beta1)
	b2 = alpha0 * beta1*beta2 + ....

	b_ = M alpha_

	'''	
	a = [1, -1.7836, 0.7859]
	b = [20.4317, 19.9046]

	# 18.8796 / (1 - 0.7947)
	# 1.5521 / (1 - 0.9890)

	alpha, beta = ab_to_alphabeta(a,b)

	print alpha, ' ?= ', 18.8796, 1.5521
	print beta, ' ?= ', 0.7947, 0.9890


def convolve(a, b, q, u, k):
	# a[0] = 1
	# q[k] = 
	return -1.*(a[1]*q[k-1] + a[2]*q[k-2]) + b[0]*u[k] + b[1]*u[k-1]
	# q[k] = -1.*sum([a[i]*q[k-i] for i in range(1,3)] + sum([b[i]*u[k-i] for i in range(2)]



def upstream_flow():
	"""
	flow from upstrean convolved with two instantaneous unit hydrographs
	"""
	K = 20
	q = numpy.empty((K))
	q[0] = 1.
	q[1] = 1.
	u = numpy.random.lognormal(size=(K)) # flow_upstream
	a = [1, -1.7836, 0.7859]
	b = [20.4317, -19.9046]
	for k in range(2,K):
		q[k] = convolve(a, b, q, u, k)

	print q
	
	import matplotlib.pylab as plt
	plt.plot(q, label='q')
	plt.plot(u, label='u')
	plt.legend()
	plt.show()

	




def lateral_flow():
	"""
	effective rainfall convolved with an instantaneous unit hydrograph
	"""

def rating_curve():
	"""
	Cross section and velocity gives flow.
	"""


def flow():

	flow = upstream_flow() + lateral_flow()

	level = rating_curve(flow)


	'''
	"Computation of the instantaneous unit hydrograph and identifiable component flow with application to two small upload catchment"
	----------------------------------------------

	h(t) is instantaneous unit hydrograph
	Q(t) is flow
	u(t) is point or spatially-averaged rainfall excess

	(1) flow via convolution:
	Q(t) = \int_0^t h(t-s) u(s) ds 
	discrete 
	Q[k] = sum([ h[i]*u[k-i] for i in range(k) ]) + xi[k]
	stabilize
	B[M], A[N] with A[0]=1
	Q[k] = sum([ B[i]*u[k-i] for i in range(m) ])/sum([ A[i]*u[k-i] for i in range(n) ]) + xi[k]

	q[k] = a_1 

	Q[k] = sum([ B[i]*u[k-i] for i in range(m) ])/sum([ A[i]*u[k-i] for i in range(n) ]) + xi[k]
	steady state gain is B[0]/A[0]

	(2) modulation of the measured rainfall r at time step k by a temperature dependent factor to compensate for evapotranspiration losses
	rs[k] = r[k] * (t_m - t[k]) / t_m # t_m ref temp greater than max 

	(3) adjustment which allows for antecedent precipitation effects on the soil moisture
	s[k] = s[k-1] + (rs[k] - s[k-1]) / tau # tau parameter

	(4) effictive rainfall
	u[k] = c * rs[k] * s[k] # c parameter


	'''


	# Q[t] = sum([Qs[i,t] for i in range(len(Qs))])

	# Qs[i,t] = beta[i] * U[t] * A - alpha[i] * Q[i, t-1]


def redesigned_effective_rainfall():
	'''
	"Redesign of the IHACRES rainfall-runoff model"
	----------------------------------------------

	u[k] effective rainfall

	I soil moisture index
	c mass balance
	p non-linear response
	phi[k] soil moisture
	r[k] observed rainfall

	tau[k] drying rate

	tau_w drying rate
	T_m temperature modulation
	T_r temperature reference
	'''

	# (3)
	tau[k] = tau_w * numpy.exp(0.62 * T_m * (T_r - T[k]) )

	# (2)
	phi[k] = r[k] + (1-1/tau[k]) * phi[k-1]

	# (1)
	u[k] = r[k] * ( c * (phi[k] -I) )**p 




if __name__ == '__main__':
	test_ab_to_alphabeta()
	upstream_flow()

