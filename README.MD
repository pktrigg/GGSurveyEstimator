# ABOUT
## GGSurvey Estimator is a pure python toolbox designed to efficiently estimate hydrographic surveys.
* It is designed to run within the *toolbox* framework of ArcGISPro 2.1 or higher.
* It is made available under GPL3 opensource licence
* It is available for download from https://github.com/pktrigg/GGSurveyEstimator
* The basic flow is as follows:
  * User need to have a featureclass (a layer in the map), which contains polygons to be estimated.  This is typically in the form of a geodatabase or shapefile.  The area need to be a polgon, not a polyline.  The featureclass can be either geographicals or grid.  The tool will interrogate the spatial reference of the featureclass and determine what it is and handle it either way.
  * User uses the regular selection tool to select ONE polygon for estimation (need to do one at a time, so the algorithm can compute centroids, clipping boundaries etc)
  * In the geoprocessing pane, User selects the toolbox.  It is called GGSurveyEstimator.pyt.  Browse for it and double click to launch. The user interface should appear as a geoprocessing dialog, with a few parameters required to run the estimation.
  * Select the feature layer which contains the selected polygon for processing. By default, there will be a red cross indicating you really need to select this as the primary input.
  * Enter the line spacing in metres.  The line spacing is a key parameter for any estimation.  This is typically computed as a multiplication of teh water daeth * the sonar coverage rate, ie 4 times water depth, so in 50m water with a 4 times wate depth sonar, you can survey with full coverage at 50 * 4 = 200m line spacing
  * Enter the primary survey line spacing in metres. This will be used in the computation of the line plans.
  * Enter the primary survey line heading in degrees.  The primary lines will take on this orientation.  It is typical that this value is parallel to the long axis of the polygon.
  * Enter the primary survey line prefix.  This is used to automatically name each survey line.  The line name will be appended with the offset from the line, e.g. a prefix of 'MainLine' will be appeneded to 'MainLine_P100' for an offset line 100m to port of the centreline.  The centreline will be called 'MainLine_Centreline'
  * Enter the vessel speed in Knots. We use knots as folks think in knots rather than SI units of metres/second.  This is used in the survey duration computations report.
  * Enter the duration of the line turn in hours.  This is used in the survey duration computations report.
  * Press # Run # to run the estimator
  * The most common problem is you have not selected a polygon in the map, or have not selected the correct layer in the dialog.  The tool will warn you if you have made this mistake.
  * The tool will display some progress in the standard geoprosessing interface, which you can expand as needed.
  *



![GitHub Logo](/images/GGSurveyEstimator1.png)


# TODO #
* add UI for xlines to be computed with default as 15 times primary line spacing
* add UI to specify GEBCO global bathy database.
* add to github
* auto compute the heading based ont the longest vector in the polygon. trigger this if the user enters -1 for the heading.

# DONE
* output featureclass is now the SSDM standard proposed survey lines FC
* sort out support for both geographical and grid input coordinate systems
* add UI for Projectname
* auto populate date
* auto populate username
* auto compute line direction
* auto populate approved by, date
* write the results to a CSV file
* add the new FC to the map and display the results
* Compute the long axis bearing.  If the user sets 0 as the bearing, we can auto compute the bearing
* refresh the map
* add the new FC to the map
* clearly delineate the output for each run.
* add UI for PREFIX
* clip the lines ot the polygon
* validate there is a selected polygon.  If not, report something friendly to the user
* Basic User Inteface using Geoprocessing UI from ESRI
* Basic script which runs inside ArcGISPro
* if there is a polygon, find the CRS, extents, and long axis, report this
* compute the lines based ont the long axis and the polygon
