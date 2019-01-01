import os.path
import sys
import math
from argparse import ArgumentParser
import numpy as np
from netCDF4 import Dataset
#from scipy.interpolate import RectBivariateSpline


#Within the 1D netCDF file, the grid is stored as a one-dimensional array of 2-byte signed integer values of elevation in metres, with negative values for bathymetric depths and positive values for topographic heights.
#The complete data set gives global coverage.
#The grid consists of 21,600 rows x 43,200 columns, resulting in 933,120,000 data points.
#The data start at the Northwest corner of the file and are arranged in latitudinal bands of 360 degrees x 120 points per degree = 43,200 values.
#The data range eastward from 179° 59' 45'' W to 179° 59' 45'' E.
#Thus, the first band contains 43,200 values for 89° 59' 45'' N, then followed by a band of 43,200 values at 89° 59' 15'' N and so on at 30 arc second latitude intervals down to 89° 59' 45'' S.
#The data values are pixel centre registered i.e. they refer to elevations at the centre of grid cells.
#This grid file format is suitable for use with the GEBCO Digital Atlas Software Interface and GEBCO Grid display software and packages such as Generic Mapping Tools (GMT).

def main():

	parser = ArgumentParser(description='Read GEBCO Bathymetry 1D NetCDF File and extract depths.')
	parser.add_argument('-i', dest='inputFile', action='store', default='GEBCO_2014_1D.nc', help='-i <GEBCO_2014_1D.nc> : input filename to process.')
	parser.add_argument('-o', dest='outputFile', action='store', default='bathy.csv', help='-o <bathy.csv> : output filename to create. e.g. bathy.csv [Default: bathy.csv]')
	parser.add_argument('-s', dest='step', action='store', default='1', help='-s <step size in multiples of the GEBCO interval (about 150m)> : decimate the data to reduce the output size. [Default: 30]')
	parser.add_argument('-x1', dest='x1', action='store', default=110, help='bounding box topleft X. [Default: 110]')
	parser.add_argument('-y1', dest='y1', action='store', default=-30, help='bounding box top left Y. [Default: -30]')
	parser.add_argument('-x2', dest='x2', action='store', default=115, help='bounding box bottom right X. [Default: 115]')
	parser.add_argument('-y2', dest='y2', action='store', default=-35, help='bounding box bottom right Y. [Default:-35]')

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)

	args = parser.parse_args()

	gebco = GEBCOReader(args.inputFile)
	# boundingBox = [[110,-30], [115,-35]] #top left, bottom right.
	boundingBox = [[float(args.x1), float(args.y1)], [float(args.x2), float(args.y2)]]
	gebco.loadBoundingBoxDepths(boundingBox, float(args.step))
	gebco.exportDepthsToCSV(args.outputFile)

class GEBCOReader:
	'''Class to read a GEBCO 1D global bathymetry file, rapidly access the data at any given coordinate'''
	def __init__(self, fileName):
		if not os.path.isfile(fileName):
			print ("file not found:", fileName)
		self.fileName = fileName

		self.nc = Dataset(fileName, 'r', Format='NETCDF4')
		# print(self.nc.variables)

		# get coordinates variables
		self.longitudeVariable = self.nc.variables['x_range'][:]
		self.latitudeVariable = self.nc.variables['y_range'][:]
		self.zVariable = self.nc.variables['z_range'][:]
		self.spacing = self.nc.variables['spacing'][:]
		self.dimension = self.nc.variables['dimension'][:]

		self.longitude = []
		self.latitude = []
		self.depths = []
		return

	def loadBoundingBoxDepths(self, boundingBox, stepSize):
		'''load a bounding box from the GEBCO dataset into a numpy array so we can interpolate and access the depths with ease. Bounding box is top left and bottom right in the format:[[x1,y1,[x2,y2]]'''

		#add a couple of extra grid nodes to ensure we have good coverage.
		boundingBox[0][0] -= self.spacing[0]
		boundingBox[0][1] += self.spacing[1]
		boundingBox[1][0] += self.spacing[0]
		boundingBox[1][1] -= self.spacing[1]

		self.latitude = np.arange(boundingBox[1][1], boundingBox[0][1], self.spacing[1] * stepSize)
		self.longitude = np.arange(boundingBox[0][0], boundingBox[1][0], self.spacing[0] * stepSize)

		for lat in np.nditer(self.latitude):
			d=[]
			for lon in np.nditer(self.longitude):
				idx = self.coordinate2Index(lat, lon)
				z = self.nc.variables['z'][idx]
				d.append(z)
			self.depths.append(d)

		print ("depths records loaded: %d" % (len(self.longitude) * len(self.latitude)))

	def exportDepthsToCSV(self, fileName):
		print("Writing data to:%s..." % (fileName))
		f = open(fileName, "w")
		row = 0
		for lat in np.nditer(self.latitude):
			col = 0
			for lon in np.nditer(self.longitude):
				f.write("%.8f, %.8f, %.1f\n" % (lon, lat, self.depths[row][col]))
				col += 1
			row += 1
		f.close()
		return

	def coordinate2Index(self, latitude, longitude):
		'''convert a latitude/longitude into the 1D index used to access the GEBCO bathymetry'''
		#The grid consists of 21,600 rows x 43,200 columns, resulting in 933,120,000 data points.
		#The data start at the Northwest corner of the file and are arranged in latitudinal bands of 360 degrees x 120 points per degree = 43,200 values.
		#latitudinal bands of 360 degrees x 120 points per degree = 43,200 values.
		#arrays start at the northwest of the planet...

		row = round((90 - latitude) / self.spacing[0])
		col = round((longitude + 180) / self.spacing[1])
		idx = clamp(row * self.dimension[0] + col, 0, (self.dimension[0] * self.dimension[1]))
		return idx

	def close(self):
		self.nc.close()

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

if __name__ == "__main__":
		main()

##### scipy interpolator  not yet implemented####
	# def InterpolateDepths():
	# 	'''we may need to interpolate depths so we can work in smaller areas.  This is not ideal, but gebco is the best we have'''
	# 	# latitude = np.array([1,2,3,4])
	# 	# longitude = np.array([1,2,3,4,5])
	# 	# depths = np.array([
	# 	# 	[4,1,4,4,2],
	# 	# 	[4,2,2,999,6],
	# 	# 	[3,7,4,3,5],
	# 	# 	[2,4,5,3,4]
	# 	# ])
	# 	# grid = RectBivariateSpline(latitude, longitude, depths)

	# def GetDepthAt(self, latitude, longitude):
	# 	z = grid.__call__(1,1)
	# 	return grid

#####END OF BLOCK####
