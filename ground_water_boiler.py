'''
Setup
-----------------------------------
1. Download 
[MODFLOW](http://water.usgs.gov/ogw/modflow/MODFLOW.html)
and
[Flopy](https://github.com/modflowpy/flopy)
2. Install MODFLOW [(instructions)](http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/readme.txt)
3. Start with /flopy-master/examples/Tutorials/Tutorial02/tutorial02.py [(documentation)](http://modflowpy.github.io/flopydoc/tutorial2.html)
'''
import numpy as np
import flopy
import multiprocessing

def run_modflow(plot=False):

    # Model domain and grid definition
    Lx = 1000.
    Ly = 1000.
    ztop = 0.
    zbot = -50.
    nlay = 3
    nrow = 10
    ncol = 10
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
    # Note that changes from the previous tutorial!
    ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
    strt = 10. * np.ones((nlay, nrow, ncol), dtype=np.float32)

    # Time step parameters
    nper = 3
    perlen = [1, 100, 100]
    nstp = perlen
    steady = [True, False, False]

    # Flopy objects
    model_name = 'tutorial2'
    MODFLOW_executable = '/home/mikey/Desktop/Backup 2015/gac/GAC/pymake/pymade'
    model_dir = "MODFLOW_IO/"+model_name+"/"
    model_name += str(multiprocessing.current_process().name)
    mf = flopy.modflow.Modflow(model_name, exe_name=MODFLOW_executable, model_ws=model_dir)
    dis = flopy.modflow.ModflowDis(mf, nlay, nrow, ncol, delr=delr, delc=delc,
                                   top=ztop, botm=botm[1:],
                                   nper=nper, perlen=perlen, nstp=nstp,
                                   steady=steady)
    bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)
    lpf = flopy.modflow.ModflowLpf(mf, hk=hk, vka=vka, sy=sy, ss=ss, laytyp=laytyp)
    pcg = flopy.modflow.ModflowPcg(mf)

    # [lay, row, col, stage, cond, rbot]

    # Make list for stress period 1
    stageleft = 10.
    stageright = 10.
    rbot = -5.
    bound_sp1 = []
    for il in range(nlay):
        condleft = hk * (stageleft - zbot) * delc
        condright = hk * (stageright - zbot) * delc
        for ir in range(nrow):
            bound_sp1.append([il, ir, 0, stageleft, condleft, rbot])
            bound_sp1.append([il, ir, ncol - 1, stageright, condright, rbot])
    print('Adding ', len(bound_sp1), 'RIVs for stress period 1.')

    # Make list for stress period 2
    stageleft = 10.
    stageright = 0.
    condleft = hk * (stageleft - zbot) * delc
    condright = hk * (stageright - zbot) * delc
    bound_sp2 = []
    for il in range(nlay):
        for ir in range(nrow):
            bound_sp2.append([il, ir, 0, stageleft, condleft, rbot])
            bound_sp2.append([il, ir, ncol - 1, stageright, condright, rbot])
    print('Adding ', len(bound_sp2), 'RIVs for stress period 2.')

    # We do not need to add a dictionary entry for stress period 3.
    # Flopy will automatically take the list from stress period 2 and apply it
    # to the end of the simulation
    stress_period_data = {0: bound_sp1, 1: bound_sp2}

    # # Create the flopy ghb object
    # ghb = flopy.modflow.ModflowGhb(mf, stress_period_data=stress_period_data)
    riv = flopy.modflow.ModflowRiv(mf, stress_period_data=stress_period_data)

    # Create the well package
    # Remember to use zero-based layer, row, column indices!
    pumping_rate = -500.
    wel_sp1 = [[0, nrow/2 - 1, ncol/2 - 1, 0.]]
    wel_sp2 = [[0, nrow/2 - 1, ncol/2 - 1, 0.]]
    wel_sp3 = [[0, nrow/2 - 1, ncol/2 - 1, pumping_rate]]
    stress_period_data = {0: wel_sp1, 1: wel_sp2, 2: wel_sp3}
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

    # import flopy.utils.binaryfile as bf

    # Create the headfile and budget file objects
    headobj = flopy.utils.binaryfile.HeadFile(model_dir+model_name+'.hds')
    # times = headobj.get_times()
    cbb = flopy.utils.binaryfile.CellBudgetFile(model_dir+model_name+'.cbc')

    if plot:

        # Imports
        import matplotlib.pyplot as plt


        # Setup contour parameters
        levels = np.linspace(0, 10, 11)
        print('Levels: ', levels)
        # extent = (delr/2., Lx - delr/2., delc/2., Ly - delc/2.)
        # print('Extent: ', extent)

        # Well point
        wpt = ((float(ncol/2)-0.5)*delr, (float(nrow/2-1)+0.5)*delc)
        wpt = (450., 550.)

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
            qm = modelmap.plot_bc('RIV', alpha=0.5)
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

        plt.show()

        # Plot the head versus time
        idx = (0, nrow/2 - 1, ncol/2 - 1)
        ts = headobj.get_ts(idx)
        plt.subplot(1, 1, 1)
        ttl = 'Head at cell ({0},{1},{2})'.format(idx[0] + 1, idx[1] + 1, idx[2] + 1)
        plt.title(ttl)
        plt.xlabel('time')
        plt.ylabel('head')
        plt.plot(ts[:, 0], ts[:, 1])
        plt.show()

    return headobj.get_alldata(), cbb.get_data(text='FLOW RIGHT FACE', kstpkper=(99,2))[0]

if __name__ == '__main__':
    heads, flows = run_modflow(plot=True)
