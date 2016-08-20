import os

# install flopy
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'no_git', 'flopy'))

os.environ['CACHE_DIR'] = "/Volumes/PATRIOT/cache"

downloaded_data = "/Volumes/PATRIOT/downloaded_data"

# Geocentric_Datum_of_Australia_1994
boundary_file = os.path.join(downloaded_data, "Campaspe_GC/Campaspe_GCU.shp")
bore_file = os.path.join(downloaded_data, "ngis_shp_VIC/NGIS_Bores.shp")
river_file = os.path.join(downloaded_data, "SH_Network_GDB/SH_Network.gdb")

"""
TODO check geo ref system is consistant, it isn't often stored in geojson
"""

import numpy as np
import flopy
import flopy.utils.binaryfile 

# import multiprocessing
import data.boundary
import data.wells
import data.streams


def run():
    # bounding box
    bbox = data.boundary.get_bounding_box(boundary_file)
    min_x, max_x, min_y, max_y = bbox["bbox"]
    # boundary_file_wkt = bbox["ref"]

    Lx = max_x - min_x
    Ly = max_y - min_y
    ztop = 0.
    zbot = -50.
    nlay = 1
    nrow = 40
    ncol = 20
    delr = Lx / ncol
    delc = Ly / nrow
    delv = (ztop - zbot) / nlay
    botm = np.linspace(ztop, zbot, nlay + 1)
    hk = 1.
    vka = 1.
    sy = 0.1
    ss = 1.e-4
    laytyp = 1


    # Variables for the BAS package
    ibound = data.boundary.get_ibound(boundary_file=boundary_file, bbox=bbox, nrow=nrow, ncol=ncol, delr=delr, delc=delc)
    strt = 10. * np.ones((nlay, nrow, ncol), dtype=np.float32)


    # TODO
    streams = data.streams.make_riv(river_file=river_file, boundary_file=boundary_file, bbox=bbox, nrow=nrow, ncol=ncol, delr=delr, delc=delc)
    stream_array = streams['raster']
    reaches = streams['reaches']
    print streams['heads']
    print streams['tips']


    import matplotlib.pylab as plt
    plt.imshow(stream_array, interpolation=None)
    plt.colorbar()
    plt.show()
    print len(reaches), "len(reaches)"


    well_density = data.wells.wells_in_boundary(bore_file=bore_file, boundary_file=boundary_file, bbox=bbox, nrow=nrow, ncol=ncol, delr=delr, delc=delc)
    well_density = np.array(well_density, dtype=np.float)
    # print "np.sum(well_density)", np.sum(well_density)
    wells = []
    unwells = []
    pumping_rate = -1.  # will be multiplied by density
    for i in range(well_density.shape[0]):
        for j in range(well_density.shape[1]):
            wells.append([0, i, j, pumping_rate * well_density[i, j]])
            unwells.append([0, i, j, 0])


    # Time step parameters
    nper = 3
    perlen = [1, 180, 180]  # An array of the stress period lengths (in days if default itmuni = 4).
    nstp = [1, 180, 180]  # Number of time steps in each stress period (default is 1).
    steady = [True, False, False]

    # Flopy objects
    modelname = 'campaspe'
    model_ws = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'no_git', 'modflow_io', modelname)
    # model_ws += str(multiprocessing.current_process().name) # so each process has own files
    mf = flopy.modflow.Modflow(modelname, exe_name='mf2005', model_ws=model_ws)
    dis = flopy.modflow.ModflowDis(mf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc,
                                   top=ztop, botm=botm[1:],
                                   nper=nper, perlen=perlen, nstp=nstp,
                                   steady=steady)
    bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)
    lpf = flopy.modflow.ModflowLpf(mf, hk=hk, vka=vka, sy=sy, ss=ss, laytyp=laytyp)
    pcg = flopy.modflow.ModflowPcg(mf)

    # Make list for stress period 1
    stageleft = 10.
    stageright = 10.
    bound_sp1 = []
    for il in range(nlay):
        condleft = hk * (stageleft - zbot) * delc
        condright = hk * (stageright - zbot) * delc
        for ir in range(nrow):
            bound_sp1.append([il, ir, 0, stageleft, condleft])
            bound_sp1.append([il, ir, ncol - 1, stageright, condright])
    print('Adding ', len(bound_sp1), 'GHBs for stress period 1.')

    # Make list for stress period 2
    stageleft = 10.
    stageright = 0.
    condleft = hk * (stageleft - zbot) * delc
    condright = hk * (stageright - zbot) * delc
    bound_sp2 = []
    for il in range(nlay):
        for ir in range(nrow):
            bound_sp2.append([il, ir, 0, stageleft, condleft])
            bound_sp2.append([il, ir, ncol - 1, stageright, condright])
    print('Adding ', len(bound_sp2), 'GHBs for stress period 2.')

    # We do not need to add a dictionary entry for stress period 3.
    # Flopy will automatically take the list from stress period 2 and apply it
    # to the end of the simulation
    stress_period_data = {0: bound_sp1, 1: bound_sp2}

    # Create the flopy ghb object
    ghb = flopy.modflow.ModflowGhb(mf, stress_period_data=stress_period_data)

    # Create the well package
    # Remember to use zero-based layer, row, column indices!
    # pumping_rate = -500.
    # wel_sp1 = [[0, nrow/2 - 1, ncol/2 - 1, 0.]]
    # wel_sp2 = [[0, nrow/2 - 1, ncol/2 - 1, 0.]]
    # wel_sp3 = [[0, nrow/2 - 1, ncol/2 - 1, pumping_rate]]
    stress_period_data = {0: unwells, 1: wells, 2: unwells}
    wel = flopy.modflow.ModflowWel(mf, stress_period_data=stress_period_data)

    # Output control
    stress_period_data = {(0, 0): ['save head',
                                   'save drawdown',
                                   'save budget',
                                   'print head',
                                   'print budget']}
    save_head_every = 1
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=stress_period_data,
                                 compact=True)

    # Write the model input files
    mf.write_input()

    # Run the model
    success, mfoutput = mf.run_model(silent=False, pause=False)
    if not success:
        raise Exception('MODFLOW did not terminate normally.')

    # Create the headfile and budget file objects
    headobj = flopy.utils.binaryfile.HeadFile(os.path.join(model_ws, modelname + '.hds'))
    # times = headobj.get_times()
    cbb = flopy.utils.binaryfile.CellBudgetFile(os.path.join(model_ws, modelname + '.cbc'))

    return headobj, cbb, mf


def plot(headobj, cbb, mf):
    # Imports
    import matplotlib.pyplot as plt
    
    delr = mf.dis.delr[0]
    delc = mf.dis.delc[0]
    nrow, ncol, nlay, nper = mf.nrow_ncol_nlay_nper
    Lx = delr * ncol
    Ly = delc * nrow

    # Setup contour parameters
    levels = np.linspace(0, 10, 11)
    extent = (delr / 2., Lx - delr / 2., delc / 2., Ly - delc / 2.)
    print('Levels: ', levels)
    print('Extent: ', extent)

    # Well point
    min_x, max_x, min_y, max_y = data.boundary.get_bounding_box(boundary_file)["bbox"]
    wpt = ((float(ncol / 2) - 0.5) * delr, (float(nrow / 2 - 1) + 0.5) * delc)
    print wpt
    # wpt = (450., 550.)

    # Make the plots
    mytimes = [1.0, 101.0, 201.0]
    for iplot, time in enumerate(mytimes):
        print('*****Processing time: ', time)
        head = headobj.get_data(totim=time)
        #Print statistics
        print('Head statistics')
        print('  min: ', head.min())
        print('  max: ', head.max())
        print('  std: ', head.std())

        # Extract flow right face and flow front face
        frf = cbb.get_data(text='FLOW RIGHT FACE', totim=time)[0]
        fff = cbb.get_data(text='FLOW FRONT FACE', totim=time)[0]

        #Create the plot
        #plt.subplot(1, len(mytimes), iplot + 1, aspect='equal')
        plt.subplot(1, 1, 1, aspect='equal')
        plt.title('stress period ' + str(iplot + 1))


        modelmap = flopy.plot.ModelMap(model=mf, layer=0)
        qm = modelmap.plot_ibound()
        lc = modelmap.plot_grid()
        qm = modelmap.plot_bc('GHB', alpha=0.5)
        cs = modelmap.contour_array(head, levels=levels)
        plt.clabel(cs, inline=1, fontsize=10, fmt='%1.1f', zorder=11)
        quiver = modelmap.plot_discharge(frf, fff, head=head)


        mfc = 'None'
        if (iplot+1) == len(mytimes):
            mfc='black'
        plt.plot(wpt[0], wpt[1], lw=0, marker='o', markersize=8, 
                 markeredgewidth=0.5,
                 markeredgecolor='black', markerfacecolor=mfc, zorder=9)
        plt.text(wpt[0]+25, wpt[1]-25, 'well', size=12, zorder=12)
        plt.show()


    # Plot the head versus time
    idx = (0, nrow / 2 - 1, ncol / 2 - 1)
    ts = headobj.get_ts(idx)
    plt.subplot(1, 1, 1)
    ttl = 'Head at cell ({0},{1},{2})'.format(idx[0] + 1, idx[1] + 1, idx[2] + 1)
    plt.title(ttl)
    plt.xlabel('time')
    plt.ylabel('head')
    plt.plot(ts[:, 0], ts[:, 1])
    plt.show()


if __name__ == '__main__':
    plot(*run())
