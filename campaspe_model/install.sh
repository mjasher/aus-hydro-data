# compile modflow
# the resulting binary doesn't play nicely: flopy/flopy/utils/binaryfile.py:175: RuntimeWarning: overflow encountered in int_scalars self.databytes = header['ncol'] * header['nrow'] * self.realtype(1).nbytes 

# git clone git@github.com:modflowpy/pymake.git
# export PYTHONPATH=/Users/masher/Desktop/phd/campaspe/pymake
# python3 pymake/examples/make_mf2005.py
# sudo ln -s /Users/masher/Desktop/phd/campaspe/temp/mf2005dbl /usr/bin/mf2005

# compile modflow
mkdir no_git
cd no_git
git clone git@github.com:mjasher/pymake.git
mkdir temp
cd temp
curl -O http://water.usgs.gov/ogw/modflow/MODFLOW-2005_v1.11.00/mf2005v1_11_00_unix.zip
unzip mf2005v1_11_00_unix.zip
python ../pymake/makebin.py -i Unix/src/ -o mf2005mja
cd ../
sudo rm /usr/bin/mf2005
sudo ln -s $(pwd)/temp/mf2005mja /usr/bin/mf2005

# install flopy

git clone git@github.com:modflowpy/flopy.git
export PYTHONPATH=$(pwd)/flopy

# run flopy example, you should see some plots

python flopy/examples/Tutorials/Tutorial02/tutorial02.py