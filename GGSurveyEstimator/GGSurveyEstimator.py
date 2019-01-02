#name:			GGSurveyEstimator
#created:	    October 2018
#by:			paul.kennedy@guardiangeomatics.com
#description:   python module to estimate a marine survey duration from a user selected polygon
#designed for:  ArcGISPro 2.2.4

# See readme.md for more details

import arcpy
import geodetic
import math

import os.path
import math
import pprint
import math
import time
from datetime import datetime
from datetime import timedelta
import os

VERSION = "4.0"

class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
		self.label = "GG Survey Estimator Toolbox"
		self.alias = "GG Survey Estimator Toolbox"

		# List of tool classes associated with this toolbox
		self.tools = [SurveyEstimatorTool]

class SurveyEstimatorTool(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "GG Hydrographic Survey Estimator"
		self.description = "Compute a hydrographic survey line plan within a selected polygon"
		self.canRunInBackground = False

	def getParameterInfo(self):
		"""Define parameter definitions"""
		# First parameter
		param0 = arcpy.Parameter(
			displayName="Feature Layer to Estimate. This is the layer containing the user selected polygon for estimation, and is critical to the computation.",
			name="in_features",
			datatype="GPFeatureLayer",
			parameterType="Required",
			direction="Input")
		param0.value = "SelectBoundaryPolygonLayer..."

		param1 = arcpy.Parameter(
			displayName="Primary Line Spacing (m) (e.g. Spacing = Depth*MBESCoverage, or -1 to compute depths based on SSDM Survey_Sounding_Grid Feature Class)",
			name="lineSpacing",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param1.value = "-1"

		param2 = arcpy.Parameter( 
			displayName="MBESCoverageMultiplier (only used when autocomputing the line spacing with the Survey_Sounding_Grid, if manually setting line spacing, ignore this. Use GGGebcoExtractor to create a sounding grid!)",
			name="MBESCoverageMultiplier",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param2.value = "4.0"

		param3 = arcpy.Parameter(
			displayName="Primary Survey Line Heading (deg)",
			name="lineHeading",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param3.value = "-1"

		param4 = arcpy.Parameter(
			displayName="LinePrefix.  This is used to populate SSDM Tables, and used to identify and remove duplicate computations",
			name="linePrefix",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param4.value = "MainLine"

		param5 = arcpy.Parameter(
			displayName="Vessel Speed in Knots.  This is used to compute the duration of the survey.",
			name="vesselSpeedInKnots",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param5.value = "4.5"

		param6 = arcpy.Parameter(
			displayName="Turn Duration (hours). This is used to compute the duration of the survey",
			name="turnDuration",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param6.value = "0.25"

		param7 = arcpy.Parameter(
			displayName="CrossLine Multiplier (e.g. 15 times primary line spacing, 0 for no crosslines) See https://github.com/pktrigg/GGSurveyEstimator",
			name="crossLineMultiplier",
			datatype="Field",
			parameterType="Required",
			direction="Input")
		param7.value = "15"

		params = [param0, param1, param2, param3, param4, param5, param6, param7]

		return params

	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		arcpy.AddMessage ("Parameter Changed")
		return

	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return

	def execute(self, parameters, messages):
		"""Compute a survey line plan from a selected polygon in the input featureclass."""

		arcpy.AddMessage ("#####GG Survey Estimator : %s #####" % (VERSION))
		sse = surveyEstimator()
		sse.compute(parameters)

		return

class surveyEstimator:
	'''Class to estimate hydrogrpahic survey durations using a polygon and some user specified criteria.  Output is a line plan and csv sheet ready for Excel.'''
	def __init__(self):
		return

	def __str__(self):
		return pprint.pformat(vars(self))

	def compute(self, parameters):
		'''computes a survey line plans using user-specified parameters and a user selected polygon in ArcGISPro'''

		clipLayerName			= parameters[0].valueAsText
		lineSpacing				= float(parameters[1].valueAsText)
		MBESCoverageMultiplier	= float(parameters[2].valueAsText)
		lineHeading				= float(parameters[3].valueAsText)
		linePrefix				= parameters[4].valueAsText
		vesselSpeedInKnots		= float(parameters[5].valueAsText)
		turnDuration			= float(parameters[6].valueAsText)
		crossLineMultiplier		= float(parameters[7].valueAsText)
		polygonIsGeographic		= False #used to manage both grid and geographical polygons, so we can compute both with ease.
		projectName				= arcpy.env.workspace
		FCName					= "Proposed_Survey_Run_Lines" #Official SSDM V2 FC name

		aprx = arcpy.mp.ArcGISProject("current")
		aprxMap = aprx.listMaps("Map")[0]
		for lyr in aprxMap.listLayers("*"):
			if lyr.getSelectionSet():
				arcpy.AddMessage ("found layerpkpk %s " % (lyr.name))				
				for sel in lyr.getSelectionSet():
					fname = 'FID'
					fields = arcpy.ListFields(lyr.name)
					for field in fields:
						if field.name == "OBJECTID":
							fname = 'OBJECTID'
					with arcpy.da.SearchCursor(lyr, [fname]) as cursor:  
						for row in cursor:  
							print(row[0])



		# show the user something is happening...
		arcpy.AddMessage ("WorkingFolder  : %s " % (arcpy.env.workspace))
		arcpy.AddMessage ("Input FeatureClass  : %s " % (clipLayerName))
		#arcpy.AddMessage ("Requested Line Spacing (m) : %s" % (lineSpacing))
		#arcpy.AddMessage ("Requested Line Heading (deg) : %s" % (lineHeading))

		spatialReference = arcpy.Describe(clipLayerName, "GPFeatureLayer").spatialReference
		arcpy.AddMessage("Spatial Reference: %s" % (spatialReference.name))
		if spatialReference.type == "Geographic":
			arcpy.AddMessage("SRType %s" % (spatialReference.type))
			polygonIsGeographic = True

		#test to ensure a GDB is attached to the project
		if not self.checkGDBExists():
			return 1
		#test to ensure the OUTPUT polyline featureclass exists in the SSDM format + create if not
		if not self.checkRunlineFCExists(FCName, spatialReference):
			return 1

		TMPName = "TempLines" #Temporary featureclass for the unclipped survey line computation loops. This gets cleared out at the end.
		self.checkRunlineFCExists(TMPName, spatialReference)

		ClippedName = "TempClipped" #Temporary featureclass for clipping results. This gets compied into the SSDM layer at the end and then cleared out
		self.checkRunlineFCExists(ClippedName, spatialReference)

		count = 0
		#need to extract the clipLayerName from the full path as the full path does NOT take into account the selected features for processing.
		sCursor = arcpy.da.SearchCursor(clipLayerName, ["SHAPE@"])
		for row in sCursor:
			count += 1
		if count > 1:
			arcpy.AddMessage ("oops, you have selected none, or more than 1 polygon.  Please try again and select only 1 polygon!")
			return 1

		sCursor = arcpy.da.SearchCursor(clipLayerName, ["SHAPE@"])
		for row in sCursor:
			arcpy.AddMessage ("Selected Polygon Centroid:")
			arcpy.AddMessage("X:%.2f Y:%.2f" % (row[0].centroid.X, row[0].centroid.Y))
			arcpy.AddMessage("ExtentXMin:%.2f ExtentXMax:%.2f" % (row[0].extent.XMin, row[0].extent.XMax))

			#remember the polygon we will be using as the clipper
			polyClipper = row

			if lineHeading == -1:
				lineHeading = self.computeOptimalHeading(polyClipper, polygonIsGeographic)

			if lineSpacing == -1:
				#MBESCoverageMultiplier = 10 #pkpk
				lineSpacing = self.computeMeanDepthFromSoundingGrid("Survey_Sounding_Grid", spatialReference, polyClipper, MBESCoverageMultiplier)

			#get the centre of the polygon...
			polygonCentroidX = row[0].centroid.X
			polygonCentroidY = row[0].centroid.Y

			#compute the long axis...
			polygonDiagonalLength = math.hypot(row[0].extent.XMax - row[0].extent.XMin, row[0].extent.YMax - row[0].extent.YMin ) / 2
			arcpy.AddMessage("Diagonal Length of input polygon: %.3f" % (polygonDiagonalLength))

			arcpy.AddMessage("Creating Survey Plan...")

			if polygonIsGeographic:
				arcpy.AddMessage ("Layer is Geographicals...")
				polygonDiagonalLength = geodetic.degreesToMetres(polygonDiagonalLength)
				arcpy.AddMessage("Diagonal Length of input polygon: %.3f" % (polygonDiagonalLength))
				# numlines = math.ceil(polygonDiagonalLength / geodetic.metresToDegrees(float(lineSpacing)))
				numlines = math.ceil(polygonDiagonalLength / float(lineSpacing))
			else:
				arcpy.AddMessage ("Layer is Grid NOT Geographicals...")
				numlines = math.ceil(polygonDiagonalLength / float(lineSpacing))
			arcpy.AddMessage ("Number of potential lines for clipping:" +str(numlines))

			# clear the previous survey lines with the same prefix, so we do not double up
			self.deleteSurveyLines(FCName, clipLayerName, linePrefix)

			# now run the computation on the PRIMARY lines...
			arcpy.AddMessage ("Computing Primary Survey Lines...")
			self.computeSurveyLines (polygonCentroidX, polygonCentroidY, lineSpacing, lineHeading, polygonDiagonalLength, polygonIsGeographic, spatialReference, linePrefix, projectName, TMPName)

			# now run the computation on the CROSS lines...
			if crossLineMultiplier > 0:
				arcpy.AddMessage ("Computing Cross Lines...")
				self.computeSurveyLines (polygonCentroidX, polygonCentroidY, lineSpacing*crossLineMultiplier, lineHeading+90, polygonDiagonalLength, polygonIsGeographic, spatialReference, linePrefix+"_X", projectName, TMPName)

			#clip the lines from the TMP to the Clipped FC
			arcpy.AddMessage ("Clipping to polygon...")

			arcpy.Clip_analysis(TMPName, polyClipper, ClippedName)
			#append the clipped lines into the final FC
			arcpy.Append_management(ClippedName, FCName)
			#clean up
			arcpy.DeleteFeatures_management(TMPName)
			arcpy.DeleteFeatures_management(ClippedName)

			# from: https://community.esri.com/thread/168531
			# now add the new layer to the map
			# Use this line if you're not sure if it's already true
			arcpy.env.addOutputsToMap = True

			aprx = arcpy.mp.ArcGISProject("current")
			aprxMap = aprx.listMaps("Map")[0]
			LayerExists = False
			for lyr in aprxMap.listLayers("*"):
				if lyr.name == FCName:
					LayerExists = True

			if LayerExists == False:
				lyrTest = arcpy.env.workspace + "\\" + FCName
				aprx = arcpy.mp.ArcGISProject("current")
				aprxMap = aprx.listMaps("Map")[0]
				aprxMap.addDataFromPath(lyrTest)

			#now export the features to a CSV...
			self.FC2CSV(FCName, vesselSpeedInKnots, turnDuration, lineSpacing, polygonIsGeographic)

		return

	def computeSurveyLines (self, polygonCentroidX, polygonCentroidY, lineSpacing, lineHeading, polygonDiagonalLength, polygonIsGeographic, spatialReference, linePrefix, projectName, FCName):
		''' compute a survey line plan and add it to the featureclass'''
		lineCount = 0
		#do the CENTRELINE
		x2, y2, x3, y3 = self.CalcLineFromPoint(polygonCentroidX, polygonCentroidY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
		lineName = linePrefix + "_Centreline"
		polyLine = self.addPolyline(x2, y2, x3, y3, FCName, spatialReference, linePrefix, lineName, float(lineHeading), projectName, lineSpacing)
		arcpy.AddMessage ("Centreline created")
		lineCount += 1

		#do the Starboard Lines
		offset = lineSpacing
		while (offset < polygonDiagonalLength):
			#newCentreX, newCentreY = self.CalcGridCoord(polygonCentroidX, polygonCentroidY, lineHeading - 90.0, offset)
			newCentreX, newCentreY = geodetic.calculateCoordinateFromRangeBearing(polygonCentroidX, polygonCentroidY, offset, lineHeading - 90.0, polygonIsGeographic)
			x2, y2, x3, y3 = self.CalcLineFromPoint(newCentreX, newCentreY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
			lineName = linePrefix + "_S" + str("%.1f" %(offset))
			polyLine = self.addPolyline(x2, y2, x3, y3, FCName, spatialReference, linePrefix, lineName, float(lineHeading), projectName, lineSpacing)
			offset = offset + lineSpacing
			lineCount += 1
			if lineCount % 25 == 0:
				arcpy.AddMessage ("Creating Starboard Survey Lines: %d" % (lineCount))

		#do the PORT Lines
		offset = -lineSpacing
		while (offset > -polygonDiagonalLength):
			#newCentreX, newCentreY = self.CalcGridCoord(polygonCentroidX, polygonCentroidY, lineHeading - 90.0, offset)
			newCentreX, newCentreY = geodetic.calculateCoordinateFromRangeBearing(polygonCentroidX, polygonCentroidY, offset, lineHeading - 90.0, polygonIsGeographic)
			x2, y2, x3, y3 = self.CalcLineFromPoint(newCentreX, newCentreY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
			lineName = linePrefix + "_P" + str("%.1f" %(offset))
			polyLine = self.addPolyline(x2, y2, x3, y3, FCName, spatialReference, linePrefix, lineName, float(lineHeading), projectName, lineSpacing)
			offset = offset - lineSpacing
			lineCount += 1
			if lineCount % 25 == 0:
				arcpy.AddMessage ("Creating Port Survey Lines: %d" % (lineCount))

		arcpy.AddMessage ("%d Lines created" % (lineCount))

	def checkGDBExists(self):
		# check the output FGDB is in place
		if os.path.exists(arcpy.env.workspace):
			extension = os.path.splitext(arcpy.env.workspace)[1]
			if extension == '.gdb':
				#arcpy.AddMessage("workspace is a gdb.  All good!")
				return True
			else:
				arcpy.AddMessage("Oops, workspace is NOT a gdb, aborting. Please ensure you are using a file geodatabase, not this: %s" % (arcpy.env.workspace))
				return False

	# def checkRunlineFCExists2(self, FCName, spatialReference):
	# 	 # check the output FC is in place and if not, make it
	# 	 # from https://community.esri.com/thread/18204
	# 	 # from https://www.programcreek.com/python/example/107189/arcpy.CreateFeatureclass_management

	# 	 # this checks the FC is in the geodatabase as defined by the worskspace at 'arcpy.env.workspace'
	# 	 #arcpy.AddMessage("Checking FC exists... %s" % (FCName))

	# 	 if not arcpy.Exists(FCName):
	# 		 arcpy.AddMessage("Creating FeatureClass: %s..." % (FCName))

	# 		 #it does not exist, so make it...
	# 		 try:
	# 			 fc_fields = (
	# 			 ("LINE_PREFIX", "TEXT", None, None, 20, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("LINE_NAME", "TEXT", None, None, 20, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("LINE_DIRECTION", "FLOAT", 7, 2, None, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("SYMBOLOGY_CODE", "LONG", 8, None, None, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("PROJECT_NAME", "TEXT", None, None, 250, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("SURVEY_BLOCK_NAME", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("PREPARED_BY", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("PREPARED_DATE", "DATE", None, None, None, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("APPROVED_BY", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("APPROVED_DATE", "DATE", None, None, None, "", "NULLABLE", "NON_REQUIRED"),
	# 			 ("LAYER", "TEXT", None, None, 255, "", "NULLABLE", "NON_REQUIRED"),
	# 			 )

	# 			 #total_start = time.clock()

	# 			 #start = time.clock()
	# 			 fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, FCName, "POLYLINE", None, None, None, spatialReference)
	# 			 #end = time.clock()
	# 			 #arcpy.AddMessage("Create Feature Class %.3f" % (end - start))

	# 			 #start = time.clock()
	# 			 for fc_field in fc_fields:
	# 				 arcpy.AddField_management(FCName, fc_field[0], fc_field[1], fc_field[2], fc_field[3], fc_field[4], fc_field[5], fc_field[6], fc_field[7])
	# 			 #end = time.clock()
	# 			 #arcpy.AddMessage("Create Fields %.3f" % (end - start))

	# 			 #start = time.clock()
	# 			 arcpy.DeleteField_management(FCName, "Id")
	# 			 #end = time.clock()
	# 			 #arcpy.AddMessage("Delete Id Field %.3f" % (end - start))

	# 			 #total_end = time.clock()
	# 			 #arcpy.AddMessage("Total %.3f" % (total_end - total_start))
	# 			 return fc
	# 		 except Exception as e:
	# 			 print(e)
	# 			 arcpy.AddMessage("Error creating FeatureClass, Aborting.")
	# 			 return False
	# 	 else:
	# 		 arcpy.AddMessage("FC %s already exists, will use it." % (FCName))
	# 		 return True

	def checkRunlineFCExists(self, FCName, spatialReference):
		# check the output FC is in place and if not, make it
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
				("LINE_PREFIX", "TEXT", None, None, 20, "", "NULLABLE", "NON_REQUIRED"),
				("LINE_NAME", "TEXT", None, None, 20, "", "NULLABLE", "NON_REQUIRED"),
				("LINE_DIRECTION", "FLOAT", 7, 2, None, "", "NULLABLE", "NON_REQUIRED"),
				("SYMBOLOGY_CODE", "LONG", 8, None, None, "", "NULLABLE", "NON_REQUIRED"),
				("PROJECT_NAME", "TEXT", None, None, 250, "", "NULLABLE", "NON_REQUIRED"),
				("SURVEY_BLOCK_NAME", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
				("PREPARED_BY", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
				("PREPARED_DATE", "DATE", None, None, None, "", "NULLABLE", "NON_REQUIRED"),
				("APPROVED_BY", "TEXT", None, None, 50, "", "NULLABLE", "NON_REQUIRED"),
				("APPROVED_DATE", "DATE", None, None, None, "", "NULLABLE", "NON_REQUIRED"),
				("LAYER", "TEXT", None, None, 255, "", "NULLABLE", "NON_REQUIRED"),
				)
				fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, FCName, "POLYLINE", None, None, None, spatialReference)
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
				fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, FCName, "POINT", None, None, None, spatialReference)
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

	def addPolyline(self, x1, y1, x2, y2, FCName, spatialReference, linePrefix, lineName, lineDirection, projectName, layerComment):
		'''add a survey line to the geodatabase'''
		#http://pro.arcgis.com/en/pro-app/arcpy/get-started/writing-geometries.htm
		cursor = arcpy.da.InsertCursor(FCName, ["SHAPE@", "LINE_PREFIX", "LINE_NAME", "LINE_DIRECTION", "PROJECT_NAME", "PREPARED_BY", "PREPARED_DATE", "REMARKS"])
		array = arcpy.Array([arcpy.Point(x1,y1), arcpy.Point(x2,y2)])
		polyline = arcpy.Polyline(array, spatialReference)

		preparedDate = datetime.now()
		userName = self.get_username()
		#limit the string size so it does not crash
		cursor.insertRow((polyline, linePrefix[:20], lineName[:20], lineDirection, projectName[:250], userName[:50], preparedDate, str(layerComment) ))
		return polyline

	def CalcLineFromPoint(self, centreX, centreY, bearing,  rng, polygonIsGeographic):
		x2, y2 = geodetic.calculateCoordinateFromRangeBearing(centreX, centreY, rng, bearing, polygonIsGeographic)
		x3, y3 = geodetic.calculateCoordinateFromRangeBearing(centreX, centreY, rng*-1.0, bearing, polygonIsGeographic)
		return (x2, y2, x3, y3)

	def CalcGridCoord(self, x1, y1, bearing, rng):
		x2 = x1 + (math.cos(math.radians(270 - bearing)) * rng)
		y2 = y1 + (math.sin(math.radians(270 - bearing)) * rng)
		return (x2, y2)

	def deleteSurveyLines(self, FCName, clipLayerName, linePrefix):
		arcpy.AddMessage("Clearing out existing lines from layer: %s with prefix %s" % (clipLayerName, linePrefix))
		whereclause = "LINE_PREFIX LIKE '%" + linePrefix + "%'"
		arcpy.SelectLayerByAttribute_management (FCName, "NEW_SELECTION", whereclause)
		arcpy.DeleteRows_management(FCName)

	def get_username(self):
		return os.getenv('username')

	def FC2CSV(self, FCName, vesselSpeedInKnots, turnDuration, lineSpacing, polygonIsGeographic):
		'''read through the featureclass and convert the file to a CSV so we can open it in Excel and complete the survey estimation process'''
		csvName = os.path.dirname(os.path.dirname(arcpy.env.workspace)) + "\\" + FCName + ".csv"
		csvName = createOutputFileName(csvName)
		arcpy.AddMessage("Writing results to file: %s" % (csvName))
		file = open(csvName, 'w')
		msg = "LineName,LineSpacing,StartX,StartY,EndX,EndY,Length(m),Heading,Speed(kts),Speed(m/s),Duration(h),TurnDuration(h),TotalDuration(h)\n"
		file.write(msg)

		entireSurveyDuration	= 0
		entireSurveyLineLength	= 0
		entireSurveyLineCount	= 0
		speed = vesselSpeedInKnots *(1852/3600) #convert from knots to metres/second
		sCursor = arcpy.da.SearchCursor(FCName, ["SHAPE@", "LINE_NAME", "LINE_DIRECTION", "REMARKS"])
		for row in sCursor:
			if polygonIsGeographic:
				lineLength = geodetic.degreesToMetres(float(row[0].length))
			else:
				lineLength = float(row[0].length)

			duration = lineLength / speed / 3600.00
			totalDuration = duration + turnDuration
			entireSurveyDuration += totalDuration
			entireSurveyLineLength += lineLength
			entireSurveyLineCount += 1
			lineSpacing = float(row[3])
			msg = str("%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n" % (row[1], lineSpacing, row[0].firstPoint.X, row[0].firstPoint.Y, row[0].lastPoint.X, row[0].lastPoint.Y, lineLength, row[2], vesselSpeedInKnots, vesselSpeedInKnots*(1852/3600), duration, turnDuration, totalDuration))
			file.write(msg)

		file.close()

		#report the entire survey stats...
		arcpy.AddMessage("Entire Survey Line Count: %d Lines" % (entireSurveyLineCount))
		arcpy.AddMessage("Entire Survey Line Length : %.2f Km" % (entireSurveyLineLength/1000))
		arcpy.AddMessage("Entire Survey Duration: %.2f Hours" % (entireSurveyDuration))
		arcpy.AddMessage("Entire Survey Duration: %.2f Days" % (entireSurveyDuration/24))


		#now open the file for the user...
		os.startfile('"' + csvName + '"')

	def computeOptimalHeading(self, polyClipper, polygonIsGeographic):
		arcpy.AddMessage("Computing Optimal Survey Heading from the selected polygon...")
		try:
			# Step through each part of the feature
			xc=[]
			yc=[]
			for poly in polyClipper:
				for part in poly:
					for pnt in part:
						if pnt:
							xc.append(pnt.X)
							yc.append(pnt.Y)
						else:
							# If pnt is None, this represents an interior ring
							print("Interior Ring:")		
			#now compute the length of each vector
			ranges=[]
			maxRange = 0
			optimalBearing = 0
			for count, item in enumerate(xc, start=1 ):
				if count < len(xc):
					rng, brg = geodetic.calculateRangeBearingFromCoordinates(xc[count-1], yc[count-1], xc[count], yc[count], polygonIsGeographic)
					if rng > maxRange:
						optimalBearing = brg
					#ranges.append([rng,brg])
			arcpy.AddMessage("*******************")
			arcpy.AddMessage("Optimal Bearing is %.2f" % (optimalBearing))
			arcpy.AddMessage("*******************")
			return optimalBearing
		except Exception as e:
			arcpy.AddMessage("Error computing optimal heading, skipping...")
			return 0

	def computeMeanDepthFromSoundingGrid(self, FCName, spatialReference, polyClipper, MBESCoverageMultiplier):
		'''iterate through all features inside the sounding_grid (if present) and compute the mean depth within the selected polygon.'''
		arcpy.AddMessage("Computing Depth within polygon...")

		if not arcpy.Exists(FCName):
			arcpy.AddMessage("%s does not exist, skipping computation of mean depth.")
		else:
			ClippedName = "TempClippedSoundings" #Temporary featureclass for clipping results. This gets compied into the SSDM layer at the end and then cleared out
			self.checkSoundingGridFCExists(ClippedName, spatialReference)
			arcpy.AddMessage ("Clipping soundings grid to survey polygon for estimation...")
			#we need to clear out the temp soundings grid in case it is run more than once...
			arcpy.DeleteFeatures_management(ClippedName)
			arcpy.Clip_analysis(FCName, polyClipper, ClippedName)

			sumZ = 0
			countZ = 0
			sCursor = arcpy.da.SearchCursor(ClippedName, ["SHAPE@", "ELEVATION"])
			for row in sCursor:
				sumZ += float(row[1])
				countZ += 1
				if countZ % 10 == 0:
					arcpy.AddMessage("ID:%d X:%.2f Y:%.2f Z:%.2f" % (countZ, row[0].centroid.X, row[0].centroid.Y, row[1]))
			if countZ > 0:
				arcpy.AddMessage("****************")
				arcpy.AddMessage("Mean Depth within Selected Polygon:%.2f Sample Count:%d" % (sumZ/countZ, countZ))
				arcpy.AddMessage("e.g. with a coverage rate of %.1f, the primary line spacing should be %.2f" % (MBESCoverageMultiplier, MBESCoverageMultiplier * sumZ/countZ))
				arcpy.AddMessage("****************")
				return math.fabs(MBESCoverageMultiplier * sumZ/countZ)
			else:
				arcpy.AddMessage("No depths found within polygon, so we failed to compute mean depth. Proceeding with line spacing of 1000m.")
				return 1000
	#def createFileGDB(self, FGDBName):
	#	# Set workspace
	#	# arcpy.env.workspace = "Z:\\home\\user\\mydata"

	#	# Set local variables
	#	# out_folder_path = "Z:\\home\\user\\mydata"

	#	# Execute CreateFileGDB
	#	arcpy.CreateFileGDB_management(out_folder_path, FGDBName)

###############################################################################
def createOutputFileName(path, ext=""):
	'''Create a valid output filename. if the name of the file already exists the file name is auto-incremented.'''
	path = os.path.expanduser(path)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if not os.path.exists(path):
		return path

	if len(ext) == 0:
		root, ext = os.path.splitext(os.path.expanduser(path))
	else:
		# use the user supplied extension
		root, ext2 = os.path.splitext(os.path.expanduser(path))

	dir		= os.path.dirname(root)
	fname	= os.path.basename(root)
	candidate = fname+ext
	index	= 1
	ls		= set(os.listdir(dir))
	while candidate in ls:
			candidate = "{}_{}{}".format(fname,index,ext)
			index	+= 1

	return os.path.join(dir, candidate)
