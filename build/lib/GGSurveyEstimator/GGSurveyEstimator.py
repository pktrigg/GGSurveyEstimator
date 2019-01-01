#name:
#created:	    October 2018
#by:			paul.kennedy@guardiangeomatics.com
#description:   python module to estimate a marine survey duration from a user selected polygon
#notes:		    See main at end of script for example how to use this
#designed for ArcGISPro 2.2.3

# See readme.md for more details

#TODO

#DONE
# sort out support for both geographical and grid input coordinate systems
# add UI for Projectname
# auto populate date
# auto populate username
# auto compute line direction
# auto populate approved by, date
# write the results to a CSV file
# add the new FC to the map and display the results
# Compute the long axis bearing.  If the user sets 0 as the bearing, we can auto compute the bearing
# refresh the map
# add the new FC to the map
# clearly delineate the output for each run.
# add UI for PREFIX
# clip the lines ot the polygon
# validate there is a selected polygon.  If not, report something friendly to the user
# Basic User Inteface using Geoprocessing UI from ESRI
# Basic script which runs inside ArcGISPro
# if there is a polygon, find the CRS, extents, and long axis, report this
# compute the lines based ont the long axis and the polygon

import arcpy
#import surveyestimator
import geodetic
import math

import os.path
import math
import pprint
#import geodetic
import math
import time
from datetime import datetime
from datetime import timedelta
import os
#import pwd

VERSION = "3.0"

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
        self.label = "Guardian Geomatics Survey Estimator"
        self.description = "Compute a survey line plan from a selected polygon"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # First parameter
        param0 = arcpy.Parameter(
            displayName="Feature Layer to Estimate",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.value = "E18045_SpectrumPolygon"

        param1 = arcpy.Parameter(
            displayName="Line Spacing (m) where Spacing = Depth*Coverage",
            name="lineSpacing",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param1.value = "1000"

        param2 = arcpy.Parameter(
            displayName="Heading (deg)",
            name="lineHeading",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.value = "0"

        param3 = arcpy.Parameter(
            displayName="LinePrefix",
            name="linePrefix",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param3.value = "MainLine"

        param4 = arcpy.Parameter(
            displayName="Vessel Speed in Knots",
            name="vesselSpeedInKnots",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param4.value = "4.5"

        param5 = arcpy.Parameter(
            displayName="turn Duration (hours)",
            name="turnDuration",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param5.value = "0.25"

        # param4 = arcpy.Parameter(
        #     displayName="Output",
        #     name="out_features",
        #     datatype="GPFeatureLayer",
        #     parameterType="Required",
        #     direction="Output")
        # param4.value = "results"
        # params = [param0, param1, param2, param3, param4]

        params = [param0, param1, param2, param3, param4, param5]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #arcpy.AddMessage ("Mean Depth :xxx")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """Compute a survey line plan from a selected polygon in the input featureclass."""

        arcpy.AddMessage ("########################GG Survey Estimator : %s ###########################" % (VERSION))
        sse = surveyEstimator()
        sse.compute(parameters)
        # sse.addToMap()
        # sse.refreshMap()
        return

class surveyEstimator:

    def __init__(self):
        return

    def __str__(self):
        return pprint.pformat(vars(self))

    def compute(self, parameters):
        '''computes a survey line plans using user-specified parameters and a user selected polygon in ArcGISPro'''

        clipLayerName           = parameters[0].valueAsText
        lineSpacing             = float(parameters[1].valueAsText)
        lineHeading             = float(parameters[2].valueAsText)
        linePrefix              = parameters[3].valueAsText
        vesselSpeedInKnots      = float(parameters[4].valueAsText)
        turnDuration            = float(parameters[5].valueAsText)
        polygonIsGeographic     = False #used to manage both grid and geographical polygons, so we can compute both with ease.
        projectName             = arcpy.env.workspace
        FCName                  = "Proposed_Survey_Run_Lines" #Official SSDM V2 FC name

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
        #testto ensure the OUTPUT polygon featureclass exists + create if not
        if not self.checkFCExists(FCName, spatialReference):
            return 1

        TMPName = "TempLines" #Temprary featureclass for the computation loops
        self.checkFCExists(TMPName, spatialReference)

        ClippedName = "TempClipped" #Temprary featureclass for clipping results into
        self.checkFCExists(ClippedName, spatialReference)

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
            arcpy.AddMessage ("Selected Polygon:")
            arcpy.AddMessage("X:%.2f Y:%.2f" % (row[0].centroid.X, row[0].centroid.Y))
            arcpy.AddMessage("ExtentXMin:%.2f ExtentXMax:%.2f" % (row[0].extent.XMin, row[0].extent.XMax))

            #remember the polygon we will be using as rthe clipper
            polyClipper = row

            #spatialReference = row[0].spatialReference #works!!
            #arcpy.AddMessage("SR %s" % (spatialReference.name))

            #get the centre of the polygon...
            polygonCentroidX = row[0].centroid.X
            polygonCentroidY = row[0].centroid.Y

            #compute the long axis...
            polygonDiagonalLength = math.hypot(row[0].extent.XMax - row[0].extent.XMin, row[0].extent.YMax - row[0].extent.YMin )
            arcpy.AddMessage("Diagonal Length of input polygon: %.3f" % (polygonDiagonalLength))

            arcpy.AddMessage("Creating Survey Plan...")


            if polygonIsGeographic:
                arcpy.AddMessage ("Layer is Geographicals...")
                numlines = math.ceil(polygonDiagonalLength / geodetic.metresToDegrees(float(lineSpacing)))
                #polygonDiagonalLength = geodetic.degreesToMetres(polygonDiagonalLength)
            else:
                arcpy.AddMessage ("Layer is Grid NOT Geographicals...")
                numlines = math.ceil(polygonDiagonalLength / float(lineSpacing))
                polygonDiagonalLength = polygonDiagonalLength
            arcpy.AddMessage ("Number of potential lines for clipping:" +str(numlines))

            #compute the bearing...
            # arcpy.AddMessage ("Selected: %.2f " % (row.Shape_Area))

            # clear the previous survey lines with the same prefix, so we do not double up
            self.deleteSurveyLines(FCName, clipLayerName, linePrefix)

            lineCount = 0
            #do the CENTRELINE
            x2, y2, x3, y3 = self.CalcLineFromPoint(polygonCentroidX, polygonCentroidY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
            lineName = linePrefix + "_Centreline"
            polyLine = self.addPolyline(x2, y2, x3, y3, TMPName, spatialReference, linePrefix, lineName, float(lineHeading), projectName)
            arcpy.AddMessage ("Centreline created")
            lineCount += 1

            #do the Starboard Lines
            offset = lineSpacing
            while (offset < polygonDiagonalLength):
                newCentreX, newCentreY = self.CalcGridCoord(polygonCentroidX, polygonCentroidY, lineHeading - 90.0, offset)
                x2, y2, x3, y3 = self.CalcLineFromPoint(newCentreX, newCentreY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
                lineName = linePrefix + "_S" + str("%.2f" %(offset))
                polyLine = self.addPolyline(x2, y2, x3, y3, TMPName, spatialReference, linePrefix, lineName, float(lineHeading), projectName)
                offset = offset + lineSpacing
                lineCount += 1
                if lineCount % 10 == 0:
                    arcpy.AddMessage ("Creating line: %d" % (lineCount))

            #do the PORT Lines
            offset = -lineSpacing
            while (offset > -polygonDiagonalLength):
                newCentreX, newCentreY = self.CalcGridCoord(polygonCentroidX, polygonCentroidY, lineHeading - 90.0, offset)
                x2, y2, x3, y3 = self.CalcLineFromPoint(newCentreX, newCentreY, lineHeading, polygonDiagonalLength, polygonIsGeographic)
                lineName = linePrefix + "_P" + str("%.2f" %(offset))
                polyLine = self.addPolyline(x2, y2, x3, y3, TMPName, spatialReference, linePrefix, lineName, float(lineHeading), projectName)
                offset = offset - lineSpacing
                lineCount += 1
                if lineCount % 10 == 0:
                    arcpy.AddMessage ("Creating line: %d" % (lineCount))


            arcpy.AddMessage ("%d Lines created" % (lineCount))

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
            self.FC2CSV(FCName, vesselSpeedInKnots, turnDuration)
        return

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

    def checkFCExists(self, FCName, spatialReference):
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

                #total_start = time.clock()

                #start = time.clock()
                fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, FCName, "POLYLINE", None, None, None, spatialReference)
                #end = time.clock()
                #arcpy.AddMessage("Create Feature Class %.3f" % (end - start))

                #start = time.clock()
                for fc_field in fc_fields:
                    arcpy.AddField_management(FCName, fc_field[0], fc_field[1], fc_field[2], fc_field[3], fc_field[4], fc_field[5], fc_field[6], fc_field[7])
                #end = time.clock()
                #arcpy.AddMessage("Create Fields %.3f" % (end - start))

                #start = time.clock()
                arcpy.DeleteField_management(FCName, "Id")
                #end = time.clock()
                #arcpy.AddMessage("Delete Id Field %.3f" % (end - start))

                #total_end = time.clock()
                #arcpy.AddMessage("Total %.3f" % (total_end - total_start))
                return fc
            except Exception as e:
                print(e)
                arcpy.AddMessage("Error creating FeatureClass, Aborting.")
                return False
        else:
            arcpy.AddMessage("FC %s already exists, will use it." % (FCName))
            return True

    def addPolyline(self, x1, y1, x2, y2, FCName, spatialReference, LINE_PREFIX, LINE_NAME, LINE_DIRECTION, PROJECT_NAME):
        '''add a survey line to the geodatabase'''
        #http://pro.arcgis.com/en/pro-app/arcpy/get-started/writing-geometries.htm
        cursor = arcpy.da.InsertCursor(FCName, ["SHAPE@", "LINE_PREFIX", "LINE_NAME", "LINE_DIRECTION", "PROJECT_NAME", "PREPARED_BY", "PREPARED_DATE"])
        array = arcpy.Array([arcpy.Point(x1,y1), arcpy.Point(x2,y2)])
        polyline = arcpy.Polyline(array, spatialReference)

        preparedDate = datetime.now() # datetime.datetime.strptime(!date!,'%d/%m/%Y %H:%M:%S')
        userName = self.get_username()
        cursor.insertRow((polyline, LINE_PREFIX, LINE_NAME, LINE_DIRECTION, PROJECT_NAME, userName, preparedDate ))
        return polyline

    def CalcLineFromPoint(self, centreX, centreY, bearing,  rng, polygonIsGeographic):

        x2, y2 = geodetic.calculateCoordinateFromRangeBearing(centreX, centreY, rng, bearing, polygonIsGeographic)
        x3, y3 = geodetic.calculateCoordinateFromRangeBearing(centreX, centreY, rng*-1.0, bearing, polygonIsGeographic)

        ##if the polygons are very small, assume geographicals.  remember this is in degrees or metres
        #x2, y2 = self.CalcGridCoord(centreX, centreY, bearing, rng) #//project fwds from the centre point
        #x3, y3 = self.CalcGridCoord(centreX, centreY, bearing, rng * -1.0) #//project backwards from the centre point

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
        #os.path.join('..','Documents and Settings',os.getlogin(),'Desktop')
        #return pwd.getpwuid( os.getuid() )[ 0 ]

    #def createFileGDB(self, FGDBName):
    #    # Set workspace
    #    # arcpy.env.workspace = "Z:\\home\\user\\mydata"

    #    # Set local variables
    #    # out_folder_path = "Z:\\home\\user\\mydata"

    #    # Execute CreateFileGDB
    #    arcpy.CreateFileGDB_management(out_folder_path, FGDBName)
    def FC2CSV(self, FCName, vesselSpeedInKnots, turnDuration):
        '''read through the featureclass and convert the file to a CSV so we can open it in Excel and complete the survey estimation process'''
        csvName = os.path.dirname(os.path.dirname(arcpy.env.workspace)) + "\\" + FCName + ".csv"
        csvName = createOutputFileName(csvName)
        arcpy.AddMessage("Writing results to file: %s" % (csvName))
        file = open(csvName, 'w')
        msg = "LineName,StartX,StartY,EndX,EndY,Length(m),Heading,Speed(kts),Speed(m/s),Duration(h),TurnDuration(h),TotalDuration(h)\n"
        file.write(msg)

        speed = vesselSpeedInKnots *(1852/3600) #convert from knots to metres/second
        sCursor = arcpy.da.SearchCursor(FCName, ["SHAPE@", "LINE_NAME", "LINE_DIRECTION"])
        for row in sCursor:
            duration = float(row[0].length) / speed / 3600
            totalDuration = duration + turnDuration
            msg = str("%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n" % (row[1], row[0].firstPoint.X, row[0].firstPoint.Y, row[0].lastPoint.X, row[0].lastPoint.Y, row[0].length, row[2], vesselSpeedInKnots, vesselSpeedInKnots*(1852/3600), duration, turnDuration, totalDuration))
            file.write(msg)

        file.close()
        #now open the file for the user...
        os.startfile('"' + csvName + '"')

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
