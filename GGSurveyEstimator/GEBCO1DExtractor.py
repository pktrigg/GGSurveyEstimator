#name:			GGGEBCOExtractor
#created:	    October 2018
#by:			paul.kennedy@guardiangeomatics.com
#description:   python module to extract GEBCO 2014 bathymetry from the NetCDF file
#designed for:  ArcGISPro 2.2.4

# See readme.md for more details

#Within the 1D netCDF file, the grid is stored as a one-dimensional array of 2-byte signed integer values of elevation in metres, with negative values for bathymetric depths and positive values for topographic heights.
#The complete data set gives global coverage.
#The grid consists of 21,600 rows x 43,200 columns, resulting in 933,120,000 data points.
#The data start at the Northwest corner of the file and are arranged in latitudinal bands of 360 degrees x 120 points per degree = 43,200 values.
#The data range eastward from 179° 59' 45'' W to 179° 59' 45'' E.
#Thus, the first band contains 43,200 values for 89° 59' 45'' N, then followed by a band of 43,200 values at 89° 59' 15'' N and so on at 30 arc second latitude intervals down to 89° 59' 45'' S.
#The data values are pixel centre registered i.e. they refer to elevations at the centre of grid cells.
#This grid file format is suitable for use with the GEBCO Digital Atlas Software Interface and GEBCO Grid display software and packages such as Generic Mapping Tools (GMT).

import arcpy
import geodetic
import math
import sys
import os.path
import math
import pprint
import math
import time
from datetime import datetime
from datetime import timedelta
import os

sys.path.append('c://infinitytool//ggtool//shared')

import geodetic
# import pyproj


from argparse import ArgumentParser
import numpy as np
from netCDF4 import Dataset
#from scipy.interpolate import RectBivariateSpline

VERSION = "3.0"

class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "GG GEBCOExtractor"
		self.alias = "GG GEBCOExtractor Toolbox"

		# List of tool classes associated with this toolbox
		self.tools = [GEBCOExtractorTool]

class GEBCOExtractorTool(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "GG GEBCO Bathymetry To SSDM"
		self.description = "Extract GEBCO Bathymetry into a standard SSDM 'Sounding_Grid' Layer using the current map view extents"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""
		# First parameter
		param0 = arcpy.Parameter(
			displayName="GEBCO Bathymetry (GEBCO_2014_1D.nc)",
			name="GEBCOBathy",
			datatype="DEFile",
			parameterType="Required",
			direction="Input")
		param0.value = r".\GGSurveyEstimator\GEBCO_2014_1D.nc"

		param1 = arcpy.Parameter(
			displayName="Decimation Factor(a multiple of the 30 second native interval from GEBCO)",
			name="Decimation",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param1.value = 10

		param2 = arcpy.Parameter(
			displayName="Top Left Latitude",
			name="TLLat",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param2.value = 10

		param3 = arcpy.Parameter(
			displayName="Top Left Longitude",
			name="TLLon",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param3.value = 76

		param4 = arcpy.Parameter(
			displayName="Lower Right Latitude",
			name="BLLat",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param4.value = 8

		param5 = arcpy.Parameter(
			displayName="Lower Right Longitude",
			name="BLLon",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param5.value = 86

		params = [param0, param1, param2, param3, param4, param5]

		return params

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return

	def execute(self, parameters, messages):
		"""Compute a survey line plan from a selected polygon in the input featureclass."""

		arcpy.AddMessage ("#####GG GEBCO Bathymetry Extractor : %s #####" % (VERSION))

		wkid				= 4326 # wkid code for wgs84
		spatialReference	= arcpy.SpatialReference(wkid)
		inputFile			= parameters[0].valueAsText
		decimation			= float(parameters[1].valueAsText)
		TLLat				= float(parameters[2].valueAsText)
		TLLon				= float(parameters[3].valueAsText)
		BLLat				= float(parameters[4].valueAsText)
		BLLon				= float(parameters[5].valueAsText)

		#open the file...
		gebco				= GEBCOReader(inputFile)

		# show the user something is happening...
		arcpy.ResetEnvironments()
		arcpy.AddMessage ("WorkingFolder  : %s " % (arcpy.env.workspace))

		#test to ensure the OUTPUT polyline featureclass exists in the SSDM format + create if not
		FCName = "Survey_Sounding_Grid" #Official SSDM V2 FC name
		if not gebco.checkSoundingGridFCExists(FCName, spatialReference):
			return 1

		#get the map extents from the current map...
		aprx = arcpy.mp.ArcGISProject("current")
		#aprxMap = aprx.listMaps("Map")[0]
		mapView = aprx.listMaps()[0]
		mapExtents=mapView.defaultCamera.getExtent()
		TL = mapExtents.upperLeft
		BR = mapExtents.lowerRight

		ptGeometry = arcpy.PointGeometry(TL, mapExtents.spatialReference)
		TLprojectedGeometry = ptGeometry.projectAs(spatialReference)

		ptGeometry = arcpy.PointGeometry(BR, mapExtents.spatialReference)
		BRprojectedGeometry = ptGeometry.projectAs(spatialReference)

		#with arcpy.da.SearchCursor(input_feature_class, fields_to_work_with) as s_cur:
		#boundingBox = [[TLprojectedGeometry.firstPoint.X, TLprojectedGeometry.firstPoint.Y], [BRprojectedGeometry.firstPoint.X, BRprojectedGeometry.firstPoint.Y]]

		# boundingBox = [[57,23], [97,1]] #top left, bottom right.
		# boundingBox = [[float(args.x1), float(args.y1)], [float(args.x2), float(args.y2)]]
		boundingBox = [[TLLon, TLLat], [BLLon, BLLat]]
		arcpy.AddMessage("Extracting GEBCO data within Map View bounding box: %.3f, %.3f, %.3f, %.3f" %(boundingBox[0][0], boundingBox[0][1], boundingBox[1][0], boundingBox[1][1], ))

		gebco.loadBoundingBoxDepths(boundingBox, decimation)

		outputFile = "c:/temp/gebcoExtraction.xyz"
		# gebco.exportDepthsToCSV(outputFile)
		gebco.DepthsToFeatureClass(FCName)

		return


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

	args.outputFile = "c:/temp/gebcoExtraction.xyz"
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

	def checkSoundingGridFCExists(self, FCName, spatialReference):
		# check the output SSDM 'sounding_grid' FC is in place and if not, make it
		# from https://community.esri.com/thread/18204
		# from https://www.programcreek.com/python/example/107189/arcpy.CreateFeatureclass_management

		# this checks the FC is in the geodatabase as defined by the worskspace at 'arcpy.env.workspace'
		#arcpy.AddMessage("Checking FC exists... %s" % (FCName))

		if not arcpy.Exists(FCName):
			arcpy.AddMessage("Creating FeatureClass: %s..." % (FCName))

			#it does not exist, so make it...
			try:
				fc_fields = (
				("LAST_UPDATE", "DATE", None, None, None, "", "NULLABLE", "NON_REQUIRED"),
				("LAST_UPDATE_BY", "TEXT", None, None, 150, "Updated By", "NULLABLE", "NON_REQUIRED"),
				("FEATURE_ID", "LONG", None, None, None, "Feature GUID", "NULLABLE", "NON_REQUIRED"),
				("SURVEY_ID", "LONG", None, None, None, "Survey Job No", "NULLABLE", "NON_REQUIRED"),
				("SURVEY_ID_REF", "TEXT", None, None, 255, "Survey Job Ref", "NULLABLE", "NON_REQUIRED"),
				("REMARKS", "TEXT", None, None, 255, "Remarks", "NULLABLE", "NON_REQUIRED"),
				("SURVEY_NAME", "TEXT", None, None, 255, "Survey Title", "NULLABLE", "NON_REQUIRED"),
				("SYMBOLOGY_CODE", "LONG", 8, None, None, "", "NULLABLE", "NON_REQUIRED"),
				("ELEVATION", "DOUBLE", None, None, 250, "Elevation or Depth", "NULLABLE", "NON_REQUIRED"),
				("LINE_NAME", "TEXT", None, None, 20, "", "NULLABLE", "NON_REQUIRED"),
				("LAYER", "TEXT", None, None, 255, "", "NULLABLE", "NON_REQUIRED"),
				)

				fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, FCName, "POINT", None, None, "ENABLED", spatialReference)
				for fc_field in fc_fields:
				 	arcpy.AddField_management(FCName, fc_field[0], fc_field[1], fc_field[2], fc_field[3], fc_field[4], fc_field[5], fc_field[6], fc_field[7])
				return fc
			except Exception as e:
				print(e)
				arcpy.AddMessage("Error creating FeatureClass, Aborting.")
				return False
		else:
			arcpy.AddMessage("FC %s already exists, will use it." % (FCName))
			return True


	def loadBoundingBoxDepths(self, boundingBox, stepSize):
		'''load a bounding box from the GEBCO dataset into a numpy array so we can interpolate and access the depths with ease. Bounding box is top left and bottom right in the format:[[x1,y1,[x2,y2]]'''

		#add a couple of extra grid nodes to ensure we have good coverage.
		#boundingBox[0][0] -= self.spacing[0] * 5
		#boundingBox[0][1] += self.spacing[1] * 5
		#boundingBox[1][0] += self.spacing[0] * 5
		#boundingBox[1][1] -= self.spacing[1] * 5

		self.latitude = np.arange(boundingBox[1][1], boundingBox[0][1], self.spacing[1] * stepSize)
		self.longitude = np.arange(boundingBox[0][0], boundingBox[1][0], self.spacing[0] * stepSize)

		for lat in np.nditer(self.latitude):
			d=[]
			for lon in np.nditer(self.longitude):
				idx = self.coordinate2Index(lat, lon)
				z = self.nc.variables['z'][idx]
				d.append(z)
			self.depths.append(d)
			arcpy.AddMessage ("Loading row for Latitude: %.3f" % (lat))

		arcpy.AddMessage ("depths records loaded: %d" % (len(self.longitude) * len(self.latitude)))

	def DepthsToFeatureClass(self, FCName):
		print("Writing data to:%s..." % (FCName))

		cursor = arcpy.da.InsertCursor(FCName, ["SHAPE@", "ELEVATION"])



		row = 0
		for lat in np.nditer(self.latitude):
			col = 0
			for lon in np.nditer(self.longitude):
				Z = float(self.depths[row][col])
				X = float(lon)
				Y = float(lat)
				pt = arcpy.Point(X,Y,Z)
				cursor.insertRow([pt, Z])
				#f.write("%.8f, %.8f, %.1f\n" % (lon, lat, self.depths[row][col]))
				col += 1
			row += 1
		return

	# def exportDepthsToCSV(self, fileName):
	# 	projection = None
	# 	arcpy.AddMessage ("Writing data to:%s..." % (fileName))
	# 	# projection = self.loadProj(32726)

	# 	#load the python proj projection object library if the user has requested it
	# 	# geo = geodetic.geodesy(args.epsg)

	# 	f = open(fileName, "w")
	# 	row = 0
	# 	for lat in np.nditer(self.latitude):
	# 		col = 0
	# 		for lon in np.nditer(self.longitude):
	# 			if projection is not None:
	# 				x,y = geo.convertToGrid(longitude, latitude)

	# 				x,y = projection(float(lon),float(lat))
	# 				f.write("%.8f,%.8f,%.1f\n" % (x, y, self.depths[row][col]))
	# 			else:
	# 				f.write("%.8f,%.8f,%.1f\n" % (lon, lat, self.depths[row][col]))
	# 			col += 1
	# 		row += 1
	# 	f.close()
	# 	return

	def loadProj(self, EPSGCode):
		'''load a pyproj object using the supplied code'''
		# wgs84=pyproj.Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth
		try:
			projection = pyproj.Proj("+init=EPSG:" + str(EPSGCode))
		except:
			return None
		return projection

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
