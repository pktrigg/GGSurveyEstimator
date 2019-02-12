# name:			GGSurveyEstimator
# created:	    October 2018
# by:			paul.kennedy@guardiangeomatics.com
# description:   python module to estimate a marine survey duration from a user selected polygon
# designed for:  ArcGISPro 2.2.4

# See readme.md for more details

import arcpy
import geodetic
import os.path
import pprint
import math
from datetime import datetime
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
        param0 = arcpy.Parameter(
            displayName="Primary Line Spacing (m) (e.g. Spacing = Depth*MBESCoverage, or -1 to compute depths based on SSDM Survey_Sounding_Grid Feature Class)",
            name="lineSpacing",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param0.value = "1000"

        param1 = arcpy.Parameter(
            displayName="MBESCoverageMultiplier (only used when autocomputing the line spacing with the Survey_Sounding_Grid, if manually setting line spacing, ignore this. Use GGGebcoExtractor to create a sounding grid!)",
            name="MBESCoverageMultiplier",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param1.value = "4.0"

        param2 = arcpy.Parameter(
            displayName="Primary Survey Line Heading (deg). Set this to -1 for the optimal line heading to be comuted, which is parallel to the long axis of the survey area.",
            name="lineHeading",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.value = "-1"

        param3 = arcpy.Parameter(
            displayName="LinePrefix.  This is used to populate SSDM Tables, and used to identify and remove duplicate computations",
            name="linePrefix",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param3.value = "MainLine"

        param4 = arcpy.Parameter(
            displayName="Vessel Speed in Knots.  This is used to compute the duration of the survey.",
            name="vesselSpeedInKnots",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param4.value = "3.5 "

        param5 = arcpy.Parameter(
            displayName="Turn Duration in Minutes. This is used to compute the duration of the survey",
            name="turnDuration",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param5.value = "10"

        param6 = arcpy.Parameter(
            displayName="CrossLine Multiplier (e.g. 15 times primary line spacing, 0 for no crosslines) See https://github.com/pktrigg/GGSurveyEstimator",
            name="crossLineMultiplier",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param6.value = "15"
        param7 = arcpy.Parameter(
            displayName="Skip the above computation and ONLY generate the reports.  This is useful when you are happy with the line plan, or after you have made subseqent edits to the line plan in ArcGIS.",
            name="GenerateReport",
            datatype="Boolean",
            parameterType="Required",
            direction="Input")
        param7.value = "False"

        params = [param0, param1, param2, param3, param4, param5, param6, param7]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        arcpy.AddMessage("Parameter Changed")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """Compute a survey line plan from a selected polygon in the input featureclass."""

        arcpy.AddMessage("#####GG Survey Estimator : %s #####" % VERSION)
        sse = SurveyEstimator()
        sse.compute(parameters)

        return


# noinspection PyMethodMayBeStatic
class SurveyEstimator:
    """Class to estimate hydrogrpahic survey durations using a polygon and some user specified criteria.  Output is a line plan and csv sheet ready for Excel."""

    def __init__(self):
        return

    def __str__(self):
        return pprint.pformat(vars(self))

    def compute(self, parameters):
        """computes a survey line plans using user-specified parameters and a user selected polygon in ArcGISPro"""

        line_spacing = float(parameters[0].valueAsText)
        mbes_coverage_multiplier = float(parameters[1].valueAsText)
        line_heading = float(parameters[2].valueAsText)
        line_prefix = parameters[3].valueAsText
        vessel_speed_in_knots = float(parameters[4].valueAsText)
        turn_duration = float(parameters[5].valueAsText) / 60.0
        cross_line_multiplier = float(parameters[6].valueAsText)
        report_action = parameters[7].valueAsText
        polygon_is_geographic = False  # used to manage both grid and geographical polygons, so we can compute both with ease.
        project_name = arcpy.env.workspace
        target_fc_name = "Proposed_Survey_Run_Lines"  # Official SSDM V2 FC name
        source_fc_name = self.get_source_feature_class_name()
        arcpy.AddMessage("ReportAction %s" % report_action)

        if source_fc_name == "":
            arcpy.AddMessage(
                "To estimate an area, please use the regular 'Select' tool in the ribbon or map tab to select a polygon.")
            arcpy.AddMessage("No selected polygon to process, exiting...")
            exit(1)

        if line_spacing == 0 or line_spacing < -1:
            arcpy.AddMessage("Please select a sensible line spacing and try again!")
            exit(1)

        if vessel_speed_in_knots < 0:
            arcpy.AddMessage("Please select a sensible vessel speed and try again!")
            exit(1)

        # show the user something is happening...
        arcpy.AddMessage("WorkingFolder  : %s " % arcpy.env.workspace)
        arcpy.AddMessage("Input FeatureClass  : %s " % source_fc_name)

        spatial_reference = arcpy.Describe(source_fc_name, "GPFeatureLayer").spatialReference
        arcpy.AddMessage("Spatial Reference: %s" % spatial_reference.name)
        if spatial_reference.type == "Geographic":
            arcpy.AddMessage("SRType %s" % spatial_reference.type)
            polygon_is_geographic = True

        if report_action == 'true':
            # now export the features to a CSV...
            self.fc_to_csv(target_fc_name, vessel_speed_in_knots, turn_duration, line_spacing, polygon_is_geographic, line_prefix)
            return

        # test to ensure a GDB is attached to the project
        if not self.check_gdb_exists():
            return 1
        # test to ensure the OUTPUT polyline featureclass exists in the SSDM format + create if not
        if not self.check_run_line_fc_exists(target_fc_name, spatial_reference):
            return 1

        tmp_name = "TempLines"  # Temporary featureclass for the unclipped survey line computation loops. This gets cleared out at the end.
        self.check_run_line_fc_exists(tmp_name, spatial_reference)

        clipped_name = "TempClipped"  # Temporary featureclass for clipping results. This gets compied into the SSDM layer at the end and then cleared out
        self.check_run_line_fc_exists(clipped_name, spatial_reference)

        # find the user selected polygon from which we can conduct the estimation.
        poly_clipper = self.get_survey_area(source_fc_name)

        if line_heading == -1:
            line_heading = self.compute_optimal_heading(poly_clipper, polygon_is_geographic)

        if line_spacing == -1:
            line_spacing = self.compute_mean_depth_from_sounding_grid("Survey_Sounding_Grid", spatial_reference, poly_clipper,
                                                                      mbes_coverage_multiplier)
            arcpy.AddMessage("LineSpacing: %.3f" % line_spacing)

        # get the centre of the polygon...
        polygon_centroid_x = poly_clipper[0].centroid.X
        polygon_centroid_y = poly_clipper[0].centroid.Y

        # compute the long axis...
        polygon_diagonal_length = math.hypot(poly_clipper[0].extent.XMax - poly_clipper[0].extent.XMin,
                                             poly_clipper[0].extent.YMax - poly_clipper[0].extent.YMin) / 2
        arcpy.AddMessage("Diagonal Length of input polygon: %.3f" % polygon_diagonal_length)

        arcpy.AddMessage("Creating Survey Plan...")

        if polygon_is_geographic:
            arcpy.AddMessage("Layer is Geographicals...")
            polygon_diagonal_length = geodetic.degreesToMetres(polygon_diagonal_length)
            arcpy.AddMessage("Diagonal Length of input polygon: %.3f" % polygon_diagonal_length)
            # numlines = math.ceil(polygonDiagonalLength / geodetic.metresToDegrees(float(lineSpacing)))
            numlines = math.ceil(polygon_diagonal_length / float(line_spacing))
        else:
            arcpy.AddMessage("Layer is Grid NOT Geographicals...")
            numlines = math.ceil(polygon_diagonal_length / float(line_spacing))
        arcpy.AddMessage("Number of potential lines for clipping:" + str(numlines))

        # clear the previous survey lines with the same prefix, so we do not double up
        self.delete_survey_lines(target_fc_name, source_fc_name, line_prefix)

        # now run the computation on the PRIMARY lines...
        arcpy.AddMessage("Computing Primary Survey Lines...")
        self.compute_survey_lines(polygon_centroid_x, polygon_centroid_y, line_spacing, line_heading, polygon_diagonal_length,
                                  polygon_is_geographic, spatial_reference, line_prefix, project_name, tmp_name)

        # now run the computation on the CROSS lines...
        if cross_line_multiplier > 0:
            arcpy.AddMessage("Computing Cross Lines...")
            hdg = geodetic.normalize360(line_heading + 90)
            self.compute_survey_lines(polygon_centroid_x, polygon_centroid_y, line_spacing * cross_line_multiplier, hdg,
                                      polygon_diagonal_length, polygon_is_geographic, spatial_reference, line_prefix + "_X",
                                      project_name, tmp_name)

        # clip the lines from the TMP to the Clipped FC
        arcpy.AddMessage("Clipping to polygon...")
        arcpy.Clip_analysis(tmp_name, poly_clipper, clipped_name)

        # append the clipped lines into the final FC
        arcpy.Append_management(clipped_name, target_fc_name)

        # clean up
        arcpy.DeleteFeatures_management(tmp_name)
        arcpy.DeleteFeatures_management(clipped_name)

        # add their resulting estimation to the map.
        self.add_results_to_map(target_fc_name)

        # now export the features to a CSV...
        self.fc_to_csv(target_fc_name, vessel_speed_in_knots, turn_duration, line_spacing, polygon_is_geographic, line_prefix)
        return

    def add_results_to_map(self, target_fc_name):
        """now add the new layer to the map"""
        arcpy.env.addOutputsToMap = True
        aprx = arcpy.mp.ArcGISProject("current")
        aprx_map = aprx.listMaps("Map")[0]
        layer_exists = False
        for lyr in aprx_map.listLayers("*"):
            if lyr.name == target_fc_name:
                layer_exists = True

        if not layer_exists:
            lyr_test = arcpy.env.workspace + "\\" + target_fc_name
            aprx = arcpy.mp.ArcGISProject("current")
            aprx_map = aprx.listMaps("Map")[0]
            aprx_map.addDataFromPath(lyr_test)
        return

    # noinspection PyMethodMayBeStatic
    def get_survey_area(self, source_fc_name):
        """read through the source featureclass and return the selected polygon for processing"""
        s_cursor = arcpy.da.SearchCursor(source_fc_name, ["SHAPE@"])
        for row in s_cursor:
            arcpy.AddMessage("Selected Polygon Centroid:")
            arcpy.AddMessage("X:%.2f Y:%.2f" % (row[0].centroid.X, row[0].centroid.Y))
            arcpy.AddMessage("ExtentXMin:%.2f ExtentXMax:%.2f" % (row[0].extent.XMin, row[0].extent.XMax))
            poly_clipper = row
            return poly_clipper
        arcpy.AddMessage("oops, no selected polygon in the source featureclass.  Please select a polygon and try again")
        return None

    def get_source_feature_class_name(self):
        """search through all the layers in the GIS and find the layer name with a selected feature. If there is no selected feature return an empty string """
        aprx = arcpy.mp.ArcGISProject("current")
        aprx_map = aprx.listMaps("Map")[0]
        try:
            for lyr in aprx_map.listLayers("*"):
                if lyr.getSelectionSet():
                    arcpy.AddMessage("found layer%s " % lyr.name)
                    return lyr.name
            arcpy.AddMessage("!!!!Oops.  No selected polygon found to process!!!!")
            return ""
        except:
            arcpy.AddMessage(
                "!!!!Oops.  Problem finding a valid layer.  Please select a polygon for processing and try again!!!!")
            return ""

    def compute_survey_lines(self, polygon_centroid_x, polygon_centroid_y, line_spacing, line_heading, polygon_diagonal_length,
                             polygon_is_geographic, spatial_reference, line_prefix, project_name, target_fc_name):
        """ compute a survey line plan and add it to the featureclass"""
        line_count = 0
        # do the CENTRELINE
        x2, y2, x3, y3 = self.calc_line_from_point(polygon_centroid_x, polygon_centroid_y, line_heading, polygon_diagonal_length,
                                                   polygon_is_geographic)
        line_name = line_prefix + "_Centreline"
        self.add_polyline(x2, y2, x3, y3, target_fc_name, spatial_reference, line_prefix, line_name,
                          float(line_heading), project_name, line_spacing)
        arcpy.AddMessage("Centreline created")
        line_count += 1

        # do the Starboard Lines
        offset = line_spacing
        while offset < polygon_diagonal_length:
            new_centre_x, new_centre_y = geodetic.calculateCoordinateFromRangeBearing(polygon_centroid_x, polygon_centroid_y,
                                                                                      offset, line_heading - 90.0,
                                                                                      polygon_is_geographic)
            x2, y2, x3, y3 = self.calc_line_from_point(new_centre_x, new_centre_y, line_heading, polygon_diagonal_length,
                                                       polygon_is_geographic)
            line_name = line_prefix + "_S" + str("%.1f" % offset)
            self.add_polyline(x2, y2, x3, y3, target_fc_name, spatial_reference, line_prefix, line_name,
                              float(line_heading), project_name, line_spacing)
            offset = offset + line_spacing
            line_count += 1
            if line_count % 25 == 0:
                arcpy.AddMessage("Creating Starboard Survey Lines: %d" % line_count)

        # do the PORT Lines
        offset = -line_spacing
        while offset > -polygon_diagonal_length:
            new_centre_x, new_centre_y = geodetic.calculateCoordinateFromRangeBearing(polygon_centroid_x, polygon_centroid_y,
                                                                                      offset, line_heading - 90.0,
                                                                                      polygon_is_geographic)
            x2, y2, x3, y3 = self.calc_line_from_point(new_centre_x, new_centre_y, line_heading, polygon_diagonal_length,
                                                       polygon_is_geographic)
            line_name = line_prefix + "_P" + str("%.1f" % offset)
            self.add_polyline(x2, y2, x3, y3, target_fc_name, spatial_reference, line_prefix, line_name,
                              float(line_heading), project_name, line_spacing)
            offset = offset - line_spacing
            line_count += 1
            if line_count % 25 == 0:
                arcpy.AddMessage("Creating Port Survey Lines: %d" % line_count)

        arcpy.AddMessage("%d Lines created" % line_count)

    def check_gdb_exists(self):
        # check the output FGDB is in place
        if os.path.exists(arcpy.env.workspace):
            extension = os.path.splitext(arcpy.env.workspace)[1]
            if extension == '.gdb':
                # arcpy.AddMessage("workspace is a gdb.  All good!")
                return True
            else:
                arcpy.AddMessage(
                    "Oops, workspace is NOT a gdb, aborting. Please ensure you are using a file geodatabase, not this: %s" % (
                        arcpy.env.workspace))
                return False

    def check_run_line_fc_exists(self, target_fc_name, spatial_reference):
        # check the output FC is in place and if not, make it
        # from https://community.esri.com/thread/18204
        # from https://www.programcreek.com/python/example/107189/arcpy.CreateFeatureclass_management

        # this checks the FC is in the geodatabase as defined by the worskspace at 'arcpy.env.workspace'
        # arcpy.AddMessage("Checking FC exists... %s" % (targetFCName))

        if not arcpy.Exists(target_fc_name):
            arcpy.AddMessage("Creating FeatureClass: %s..." % target_fc_name)

            # it does not exist, so make it...
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
                fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, target_fc_name, "POLYLINE", None, None,
                                                         None, spatial_reference)
                for fc_field in fc_fields:
                    arcpy.AddField_management(target_fc_name, fc_field[0], fc_field[1], fc_field[2], fc_field[3],
                                              fc_field[4], fc_field[5], fc_field[6], fc_field[7])
                return fc
            except Exception as e:
                print(e)
                arcpy.AddMessage("Error creating FeatureClass, Aborting.")
                return False
        else:
            arcpy.AddMessage("FC %s already exists, will use it." % target_fc_name)
            return True

    def check_sounding_grid_fc_exists(self, target_fc_name, spatial_reference):
        # check the output SSDM 'sounding_grid' FC is in place and if not, make it
        # from https://community.esri.com/thread/18204
        # from https://www.programcreek.com/python/example/107189/arcpy.CreateFeatureclass_management

        # this checks the FC is in the geodatabase as defined by the worskspace at 'arcpy.env.workspace'

        if not arcpy.Exists(target_fc_name):
            arcpy.AddMessage("Creating FeatureClass: %s..." % target_fc_name)

            # it does not exist, so make it...
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
                fc = arcpy.CreateFeatureclass_management(arcpy.env.workspace, target_fc_name, "POINT", None, None, None,
                                                         spatial_reference)
                for fc_field in fc_fields:
                    arcpy.AddField_management(target_fc_name, fc_field[0], fc_field[1], fc_field[2], fc_field[3],
                                              fc_field[4], fc_field[5], fc_field[6], fc_field[7])
                return fc
            except Exception as e:
                print(e)
                arcpy.AddMessage("Error creating FeatureClass, Aborting.")
                return False
        else:
            arcpy.AddMessage("FC %s already exists, will use it." % target_fc_name)
            return True

    def add_polyline(self, x1, y1, x2, y2, target_fc_name, spatial_reference, line_prefix, line_name, line_direction,
                     project_name, layer_comment):
        """add a survey line to the geodatabase"""
        # http://pro.arcgis.com/en/pro-app/arcpy/get-started/writing-geometries.htm
        cursor = arcpy.da.InsertCursor(target_fc_name,
                                       ["SHAPE@", "LINE_PREFIX", "LINE_NAME", "LINE_DIRECTION", "PROJECT_NAME",
                                        "PREPARED_BY", "PREPARED_DATE", "REMARKS"])
        array = arcpy.Array([arcpy.Point(x1, y1), arcpy.Point(x2, y2)])
        polyline = arcpy.Polyline(array, spatial_reference)

        prepared_date = datetime.now()
        user_name = self.get_username()
        # limit the string size so it does not crash
        cursor.insertRow((polyline, line_prefix[:20], line_name[:20], line_direction, project_name[:250], user_name[:50],
                          prepared_date, str(layer_comment)))
        return polyline

    def calc_line_from_point(self, centre_x, centre_y, bearing, rng, polygon_is_geographic):
        x2, y2 = geodetic.calculateCoordinateFromRangeBearing(centre_x, centre_y, rng, bearing, polygon_is_geographic)
        x3, y3 = geodetic.calculateCoordinateFromRangeBearing(centre_x, centre_y, rng * -1.0, bearing,
                                                              polygon_is_geographic)
        return x2, y2, x3, y3

    def calc_grid_coord(self, x1, y1, bearing, rng):
        x2 = x1 + (math.cos(math.radians(270 - bearing)) * rng)
        y2 = y1 + (math.sin(math.radians(270 - bearing)) * rng)
        return x2, y2

    def delete_survey_lines(self, target_fc_name, source_fc_name, line_prefix):
        arcpy.AddMessage("Clearing out existing lines from layer: %s with prefix %s" % (source_fc_name, line_prefix))
        whereclause = "LINE_PREFIX LIKE '%" + line_prefix + "%'"
        arcpy.SelectLayerByAttribute_management(target_fc_name, "NEW_SELECTION", whereclause)
        arcpy.DeleteRows_management(target_fc_name)

    def get_username(self):
        return os.getenv('username')

    def fc_to_csv(self, target_fc_name, vessel_speed_in_knots, turn_duration, line_spacing, polygon_is_geographic, line_prefix):
        """read through the featureclass and convert the file to a CSV so we can open it in Excel and complete the survey estimation process"""
        csv_name = os.path.dirname(os.path.dirname(arcpy.env.workspace)) + "\\" + target_fc_name + ".csv"
        csv_name = create_output_file_name(csv_name)
        arcpy.AddMessage("Writing results to file: %s" % csv_name)
        output_file = open(csv_name, 'w')
        msg = "LineName,LineSpacing,StartX,StartY,EndX,EndY,Length(m),Heading,Speed(kts),Speed(m/s),Duration(h),TurnDuration(h),TotalDuration(h)\n"
        output_file.write(msg)

        current_polygon_duration = 0
        current_polygon_line_length = 0
        current_polygon_line_count = 0

        entire_survey_duration = 0
        entire_survey_line_length = 0
        entire_survey_line_count = 0

        speed = vessel_speed_in_knots * (1852 / 3600)  # convert from knots to metres/second
        s_cursor = arcpy.da.SearchCursor(target_fc_name,
                                         ["SHAPE@", "LINE_NAME", "LINE_DIRECTION", "REMARKS", "LINE_PREFIX"])
        for row in s_cursor:
            if polygon_is_geographic:
                line_length = geodetic.degreesToMetres(float(row[0].length))
            else:
                line_length = float(row[0].length)

            duration = line_length / speed / 3600.00
            total_duration = duration + turn_duration
            entire_survey_duration += total_duration
            entire_survey_line_length += line_length
            entire_survey_line_count += 1

            prefix = row[4]
            if line_prefix in prefix:
                current_polygon_duration += duration + turn_duration
                current_polygon_line_length += line_length
                current_polygon_line_count += 1

            line_spacing = float(row[3])
            msg = str("%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n" % (
                row[1], line_spacing, row[0].firstPoint.X, row[0].firstPoint.Y, row[0].lastPoint.X, row[0].lastPoint.Y,
                line_length, row[2], vessel_speed_in_knots, vessel_speed_in_knots * (1852 / 3600), duration, turn_duration,
                total_duration))
            output_file.write(msg)

        output_file.close()

        # report the CURRENT survey stats...
        arcpy.AddMessage("##########################")
        arcpy.AddMessage("Current Polygon Line Count: %d Lines" % current_polygon_line_count)
        arcpy.AddMessage("Current Polygon Line Length : %.2f Km" % (current_polygon_line_length / 1000))
        arcpy.AddMessage("Current Polygon Duration: %.2f Hours" % current_polygon_duration)
        arcpy.AddMessage("Current Polygon Duration: %.2f Days" % (current_polygon_duration / 24))
        arcpy.AddMessage("##########################")

        # report the entire survey stats...
        arcpy.AddMessage("Entire Survey Line Count: %d Lines" % entire_survey_line_count)
        arcpy.AddMessage("Entire Survey Line Length : %.2f Km" % (entire_survey_line_length / 1000))
        arcpy.AddMessage("Entire Survey Duration: %.2f Hours" % entire_survey_duration)
        arcpy.AddMessage("Entire Survey Duration: %.2f Days" % (entire_survey_duration / 24))
        arcpy.AddMessage("##########################")

        # now open the file for the user...
        os.startfile('"' + csv_name + '"')

    def compute_optimal_heading(self, poly_clipper, polygon_is_geographic):
        arcpy.AddMessage("Computing Optimal Survey Heading from the selected polygon...")
        try:
            # Step through each part of the feature
            xc = []
            yc = []
            for poly in poly_clipper:
                for part in poly:
                    for pnt in part:
                        if pnt:
                            xc.append(pnt.X)
                            yc.append(pnt.Y)
                        else:
                            # If pnt is None, this represents an interior ring
                            print("Interior Ring:")
            # now compute the length of each vector
            max_range = 0
            optimal_bearing = 0
            for count, item in enumerate(xc, start=1):
                if count < len(xc):
                    rng, brg = geodetic.calculateRangeBearingFromCoordinates(xc[count - 1], yc[count - 1], xc[count],
                                                                             yc[count], polygon_is_geographic)
                    if rng > max_range:
                        optimal_bearing = brg
                        max_range = rng
            arcpy.AddMessage("*******************")
            arcpy.AddMessage("Optimal Bearing is %.2f" % optimal_bearing)
            arcpy.AddMessage("*******************")
            return optimal_bearing
        except:
            arcpy.AddMessage("Error computing optimal heading, skipping...")
            return 0

    def compute_mean_depth_from_sounding_grid(self, target_fc_name, spatial_reference, poly_clipper, mbes_coverage_multiplier):
        """iterate through all features inside the sounding_grid (if present) and compute the mean depth within the selected polygon."""
        arcpy.AddMessage("Computing Depth within polygon...")

        if not arcpy.Exists(target_fc_name):
            arcpy.AddMessage(
                "!!!!!!%s does not exist, skipping computation of mean depth. Will default to a 1000m line spacing soe you get some form of result!!!!!!" % (
                    target_fc_name))
            return 1000
        else:
            clipped_name = "TempClippedSoundings"  # Temporary featureclass for clipping results. This gets copied into the SSDM layer at the end and then cleared out
            self.check_sounding_grid_fc_exists(clipped_name, spatial_reference)
            arcpy.AddMessage("Clipping soundings grid to survey polygon for estimation...")
            # we need to clear out the temp soundings grid in case it is run more than once...
            arcpy.DeleteFeatures_management(clipped_name)
            arcpy.Clip_analysis(target_fc_name, poly_clipper, clipped_name)

            sum_z = 0
            count_z = 0
            s_cursor = arcpy.da.SearchCursor(clipped_name, ["SHAPE@", "ELEVATION"])
            for row in s_cursor:
                sum_z += float(row[1])
                count_z += 1
                if count_z % 10 == 0:
                    arcpy.AddMessage(
                        "ID:%d X:%.2f Y:%.2f Z:%.2f" % (count_z, row[0].centroid.X, row[0].centroid.Y, row[1]))
            if count_z > 0:
                arcpy.AddMessage("****************")
                arcpy.AddMessage("Mean Depth within Selected Polygon:%.2f Sample Count:%d" % (sum_z / count_z, count_z))
                arcpy.AddMessage("e.g. with a coverage rate of %.1f, the primary line spacing should be %.2f" % (
                    mbes_coverage_multiplier, mbes_coverage_multiplier * sum_z / count_z))
                arcpy.AddMessage("****************")
                return math.fabs(mbes_coverage_multiplier * sum_z / count_z)
            else:
                arcpy.AddMessage(
                    "No depths found within polygon, so we failed to compute mean depth. Proceeding with line spacing of 1000m.")
                return 1000


def create_output_file_name(path, ext=""):
    """Create a valid output filename. if the name of the file already exists the file name is auto-incremented."""
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

    output_dir = os.path.dirname(root)
    file_name = os.path.basename(root)
    candidate = file_name + ext
    index = 1
    ls = set(os.listdir(output_dir))
    while candidate in ls:
        candidate = "{}_{}{}".format(file_name, index, ext)
        index += 1

    return os.path.join(output_dir, candidate)
