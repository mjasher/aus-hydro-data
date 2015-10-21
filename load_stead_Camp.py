import numpy
import matplotlib.pylab as plt
import os

# import flopy 
# from flop.utils.util_array
def read1d(f, a):
    """
    Fill the 1d array, a, with the correct number of values.  Required in
    case lpf 1d arrays (chani, layvka, etc) extend over more than one line
    """
    values = []
    while True:
        line = f.readline()
        t = line.strip().split()
        values = values + t
        if len(values) >= a.shape[0]:
            break
    a[:] = numpy.array(values[0:a.shape[0]], dtype=a.dtype)
    return a

def read3d(f, a):
	nlay, nrow, ncol = a.shape
	for lay in range(nlay):
		junk = f.readline()
		for row in range(nrow):
			read1d(f, a[lay, row, :])

def read2d(f, a):
	nrow, ncol = a.shape
	junk = f.readline()
	print 'read2d', junk
	for row in range(nrow):
		read1d(f, a[row, :])
			
def read_bas(file_name, dest_file_name):
	f = open(file_name)

	junk = f.readline()
	junk = f.readline()

	nlay, nrow, ncol, nper, itmuni = [int(d) for d in f.readline().strip().split()]

	junk = f.readline()

	IAPART, ISTRT = [int(d) for d in f.readline().strip().split()]

	Ibound = numpy.empty((nlay, nrow, ncol), dtype=numpy.int32)
	for lay in range(nlay):
		junk = f.readline()
		for row in range(nrow):
		    values = []
		    while True:
		        line = f.readline()
		        t = line.replace('-1', ' -1').strip().split()
		        values = values + t
		        if len(values) >= ncol:
		            break
		    Ibound[:] = numpy.array(values[0:ncol], dtype=Ibound.dtype)

	HNOFLO = f.readline() # WRONG

	Sheads = numpy.empty((nlay, nrow, ncol), dtype=numpy.float)
	read3d(f, Sheads)

	SP = []
	for per in range(nper):
		# PERLEN NSTP TSMULT
		SP.append(f.readline().strip().split())

	numpy.savez(dest_file_name,
		nlay=nlay,
		nrow=nrow,
		ncol=ncol,
		nper=nper,
		itmuni=itmuni,
		Ibound=Ibound,
		Sheads=Sheads,
		IAPART=IAPART, 
		ISTRT=ISTRT,
		SP=SP,
	 )

def read_bcf(file_name, dest_file_name, nlay, nrow, ncol):
	f = open(file_name)

	data = f.readline().strip().split(); print "ISS", data; ISS, IBCFCB, HDRY, IWDFLG, WETFCT, IWETIT, IHDWET = data
	data = f.readline().strip().split(); print "Ltype", data; Ltype = [int(d) for d in data]
	data = f.readline().strip().split(); print "TRPY", data; TRPY = float(data[1])
	data = f.readline().strip().split(); print "DELR", data; DELR = float(data[1])
	data = f.readline().strip().split(); print "DELC", data; DELC = float(data[1])
	
	# data = f.readline().strip().split(); print data; Hy = float(data[1])

	Sf1 = numpy.empty((nlay, nrow, ncol))
	Hy = numpy.empty((nlay, nrow, ncol))
	Bot = numpy.empty((nlay, nrow, ncol))
	Vcont = numpy.empty((nlay, nrow, ncol))
	Sf2 = numpy.empty((nlay, nrow, ncol))
	Top = numpy.empty((nlay, nrow, ncol))

	lay = 0
	data = f.readline().strip().split(); print "Sf1", data; Sf1[lay,:,:] = float(data[1])
	data = f.readline().strip().split(); print "Hy", data; Hy[lay,:,:] = float(data[1])
	read2d(f, Bot[lay,:,:])
	data = f.readline().strip().split(); print "Vcont", data; Vcont[lay,:,:] = float(data[1])
	# read2d(f, Sf2[lay,:,:])
	# read2d(f, Top[lay,:,:])

	for lay in [1, 2]:
		data = f.readline().strip().split(); print "Sf1", data; Sf1[lay,:,:] = float(data[1])
		read2d(f, Hy[lay,:,:])
		read2d(f, Bot[lay,:,:])
		data = f.readline().strip().split(); print "Vcont", data; Vcont[lay,:,:] = float(data[1])
		read2d(f, Sf2[lay,:,:])
		read2d(f, Top[lay,:,:])


	for lay in [3,4,5,6]:
		data = f.readline().strip().split(); print "Sf1", data; Sf1[lay,:,:] = float(data[1])
		read2d(f, Hy[lay,:,:])
		read2d(f, Bot[lay,:,:])
		data = f.readline().strip().split(); print "Vcont", data; Vcont[lay,:,:] = float(data[1])
		data = f.readline().strip().split(); print "Sf2", data; Sf2[lay,:,:] = float(data[1])
		read2d(f, Top[lay,:,:])

	lay = 7
	data = f.readline().strip().split(); print "Sf1", data; Sf1[lay,:,:] = float(data[1])
	data = f.readline().strip().split(); print "Hy", data; Hy[lay,:,:] = float(data[1])
	read2d(f, Bot[lay,:,:])
	# data = f.readline().strip().split(); print "Vcont", data; Vcont[lay,:,:] = float(data[1])
	data = f.readline().strip().split(); print "Sf2", data; Sf2[lay,:,:] = float(data[1])
	read2d(f, Top[lay,:,:])


	numpy.savez(dest_file_name,
		Sf1=Sf1,
		Hy=Hy,
		Bot=Bot,
		Vcont=Vcont,
		Sf2=Sf2,
		Top=Top,
		ISS=ISS,
		IBCFCB=IBCFCB,
		HDRY=HDRY,
		IWDFLG=IWDFLG,
		WETFCT=WETFCT,
		IWETIT=IWETIT,
		IHDWET=IHDWET,
		Ltype=Ltype,
		TRPY=TRPY,
		DELR=DELR,
		DELC=DELC,
	 )


def read_riv(file_name, dest_file_name):
	f = open(file_name)
	
	junk = f.readline().strip().split(); print  junk;
	data = f.readline().strip().split(); print "MXRIVR:", data; MXRIVR = int(data[0])
	
	boundaries = []
	for i in range(MXRIVR):
		data = f.readline().strip().split(); 
		Layer, Row, Column = [int(d) for d in data[:3]]
		Stage, Cond, BedElev, x, y, Typ, DEM, Incision, RivStage, RivLeng, RivKfact, DefStage = [float(d) for d in data[3:]]
		Typ = int(data[8])
		boundaries.append([Layer, Row, Column, Stage, Cond, BedElev, x, y, Typ, DEM, Incision, RivStage, RivLeng, RivKfact, DefStage])

	junk = f.readline().strip().split(); print junk;

	print len(boundaries), MXRIVR
	numpy.savez(dest_file_name,
		boundaries=boundaries
	 )


def read_wel(file_name, dest_file_name):
	f = open(file_name)
	
	junk = f.readline().strip().split(); print  junk;
	data = f.readline().strip().split(); print "MXWEL:", data; MXWEL = int(data[0])
	
	boundaries = []
	for i in range(MXWEL):
		data = f.readline().strip().split(); 
		Layer, Row, Column = [int(d) for d in data[:3]]
		Q = float(data[3])
		boundaries.append([Layer, Row, Column, Q])

	junk = f.readline().strip().split(); print junk;

	print len(boundaries), MXWEL
	numpy.savez(dest_file_name,
		boundaries=boundaries
	 )


def read_drn(file_name, dest_file_name):
	f = open(file_name)
	
	junk = f.readline().strip().split(); print  junk;
	data = f.readline().strip().split(); print "MXWEL:", data; MXWEL = int(data[0])
	
	boundaries = []
	for i in range(MXWEL):
		data = f.readline().strip().split(); 
		Layer, Row, Column = [int(d) for d in data[:3]]
		Elevation, Cond, x, y = [float(d) for d in data[3:]]
		boundaries.append([Layer, Row, Column, Elevation, Cond, x, y])

	junk = f.readline().strip().split(); print junk;

	print len(boundaries), MXWEL
	numpy.savez(dest_file_name,
		boundaries=boundaries
	 )


def read_evp(file_name, dest_file_name, nlay, nrow, ncol):
	f = open(file_name)

	data = f.readline().strip().split(); print "NEVTOP", data; NEVTOP, IEVTCB = data
	data = f.readline().strip().split(); print "NEVTOP", data; INSURF, INEVTR, INEXDP, INIEVT = data[:4]

	SURF = numpy.empty((nrow, ncol))
	read2d(f, SURF)
	
	data = f.readline().strip().split(); print "EVTR", data; EVTR = float(data[1])
	
	data = f.readline().strip().split(); print "EXDP", data; EXDP = float(data[1])
	
	IEVT = numpy.empty((nrow, ncol), dtype=numpy.int)
	read2d(f, SURF)

	junk = f.readline().strip().split(); print junk;

	numpy.savez(dest_file_name,
		NEVTOP=NEVTOP, 
		IEVTCB=IEVTCB,
		INSURF=INSURF, 
		INEVTR=INEVTR, 
		INEXDP=INEXDP, 
		INIEVT=INIEVT,
		SURF=SURF,
		EVTR=EVTR,
		EXDP=EXDP,
		IEVT=IEVT,
	 )


def read_rch(file_name, dest_file_name, nlay, nrow, ncol):
	f = open(file_name)

	data = f.readline().strip().split(); print "NRCHOP IRCHCB", data; NRCHOP, IRCHCB = data[:2]
	data = f.readline().strip().split(); print "INRECH INIRCH", data; INRECH, INIRCH = data

	RCH = numpy.empty((nrow, ncol))
	read2d(f, RCH)
	
	# IRCH = numpy.empty((nrow, ncol), dtype=numpy.int)
	# read2d(f, IRCH)

	junk = f.readline().strip().split(); print junk;
	junk = f.readline().strip().split(); print junk;
	junk = f.readline().strip().split(); print junk;
	junk = f.readline().strip().split(); print junk;
	junk = f.readline().strip().split(); print junk;

	plot_layers(numpy.array([RCH]))

	numpy.savez(dest_file_name,
		NRCHOP=NRCHOP,
		IRCHCB=IRCHCB,
		INRECH=INRECH, 
		INIRCH=INIRCH,
		RCH=RCH,
		# IRCH=IRCH,
	 )


"""
def read_template(file_name, dest_file_name, nlay, nrow, ncol):
	f = open(file_name)

	data = f.readline().strip().split(); print "ISS", data; ISS, IBCFCB, HDRY, IWDFLG, WETFCT, IWETIT, IHDWET = data

	Sf1 = numpy.empty((nlay, nrow, ncol))


	lay = 0
	data = f.readline().strip().split(); print "Sf1", data; Sf1[lay,:,:] = float(data[1])
	read2d(f, Bot[lay,:,:])

	numpy.savez(dest_file_name,

	 )

"""



def plot_layers(array, title=''):
	nlay, nrow, ncol = array.shape
	for lay in range(nlay):
		in_i = array[lay,:,:] != -9999.99
		out_i = array[lay,:,:] == -9999.99
		array[lay,:,:][out_i] = -99.9999
		plt.subplot(numpy.ceil(nlay/4.), 4, lay+1)
		mean = numpy.mean(array[lay,:,:][in_i])
		std = numpy.std(array[lay,:,:][in_i])
		plt.imshow(array[lay,:,:], vmin=mean-2.*std, vmax=mean+2.*std)
		plt.colorbar()
		plt.title(title+"_"+str(lay)+"_"+str(mean))
	plt.show()


def plot_bas():
	archive = numpy.load("camp_mf_data/Camp_bas.npz")
	nlay=archive["nlay"]
	nrow=archive["nrow"]
	ncol=archive["ncol"]
	nper=archive["nper"]
	itmuni=archive["itmuni"]
	Ibound=archive["Ibound"]
	Sheads=archive["Sheads"]
	IAPART=archive["IAPART"] 
	ISTRT=archive["ISTRT"]
	SP=archive["SP"]

	print nlay, nrow, ncol

	plot_layers(Sheads)

	print 'Ibound'
	print Ibound[0,100,:]




def plot_bcf():
	archive = numpy.load("camp_mf_data/Camp_bcf.npz")
	Sf1=archive["Sf1"]
	Hy=archive["Hy"]
	Bot=archive["Bot"]
	Vcont=archive["Vcont"]
	Sf2=archive["Sf2"]
	Top=archive["Top"]
	ISS=archive["ISS"]
	IBCFCB=archive["IBCFCB"]
	HDRY=archive["HDRY"]
	IWDFLG=archive["IWDFLG"]
	WETFCT=archive["WETFCT"]
	IWETIT=archive["IWETIT"]
	IHDWET=archive["IHDWET"]
	Ltype=archive["Ltype"]
	TRPY=archive["TRPY"]
	DELR=archive["DELR"]
	DELC=archive["DELC"]

	plot_layers(Top, "Top")
	plot_layers(Bot, "Bot")
	plot_layers(Top-Bot, "T-B")
	# plot_layers(Sf1, "Sf1")
	# plot_layers(Sf2, "Sf2")
	plot_layers(Hy, "Hy")
	# plot_layers(Vcont, "Vcont")


def plot_riv(nlay, nrow, ncol):
	archive = numpy.load("camp_mf_data/Camp_riv.npz")
	boundaries=archive["boundaries"]

	riv_array = -100*numpy.ones((nlay, nrow, ncol))
	for s in boundaries:
		Layer, Row, Column, Stage, Cond, BedElev, x, y, Typ, DEM, Incision, RivStage, RivLeng, RivKfact, DefStage = s
		riv_array[Layer-1, Row-1, Column-1] += Stage

	plot_layers(riv_array)


if __name__ == '__main__':
	dir_name = "/home/mikey/Desktop/Camp/modflow"

	# read_bas(os.path.join(dir_name, 'camp.bas'), 'camp_mf_data/Camp_bas.npz')

	nlay, nrow, ncol = (8, 1677, 667)

	# read_bcf(os.path.join(dir_name, 'camp.bcf'), 'camp_mf_data/Camp_bcf.npz', nlay, nrow, ncol)

	# read_riv(os.path.join(dir_name, 'camp.riv'), 'camp_mf_data/Camp_riv.npz')

	# read_wel(os.path.join(dir_name, 'steady100.wel'), 'camp_mf_data/Camp_wel.npz')

	# read_drn(os.path.join(dir_name, 'steady2.drn'), 'camp_mf_data/Camp_drn.npz')

	# read_evp(os.path.join(dir_name, 'camp.evp'), 'camp_mf_data/Camp_evp.npz', nlay, nrow, ncol)

	# read_rch(os.path.join(dir_name, 'dpi.rch'), 'camp_mf_data/Camp_rch.npz', nlay, nrow, ncol)

	# plot_bas()
	plot_bcf()
	# plot_riv(nlay, nrow, ncol)

