# ABOUT
## GGSurvey Estimator is a pure python toolbox designed to efficiently estimate hydrographic surveys.
* It is designed to run within the *toolbox* framework of ArcGISPro 2.1 or higher.
* It is made available under GPL3 opensource licence
* It is available for download from https://github.com/pktrigg/GGSurveyEstimator

![GitHub Logo](/images/GGSurveyEstimator3.png)


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
  ![GitHub Logo](/images/GGSurveyEstimator1.png)

  * The tool will display some progress in the standard geoprosessing interface, which you can expand as needed.
  * Using the requested survey line heading, the tool will initially compute a centreline which runs directly through the centroid of the polygon.  It then uses the survey line spacing to compute a series of offset lines to port and starboard of the centreline.  Offset lines are computed parallel to the centreline, using the requested survey line heading. This technique ensures you will ALWAYS get at least 1 line through your polygon. A critical part of the computation process is the clipping of lines at the exact intersection of the line with the user-selected polygon.  This complex calculation is done for you on every survey line.
  Witht eprimary survey lines complete, the tool then computes cross lines at the user requested cross line multiplier.  This is a multiplier of the primary line spacing, and by default is the standard 15-times primary line spacing.  If you do not want crosslines, make this parameter zero.
  * As you would expect, the cross lines will be generated perpendicualr to the primary line spacing.
  * The computed survey lines are saved to a feature class 'Proposed_Survey_Lines" as defined by the OGP Seabed Survey Data Model (SSDM) V2 specificaiton.  This is the most widely used data model in the survey industry so an easy schema to work with.  If your geodabatase does not have a featureclass of name 'Proposed_Survey_Lines' one will be created for you.
  * Each survey line in the layer has a series of fields as determined by the SSDM schema.  A bunch of these fields will be filled out for you
  * On competion of the process, the results will be saved to a CSV file in the **parent folder** of the geodatabase location for you, and automatically opened in Excel. You can then complete the estimation process.

![GitHub Logo](/images/GGSurveyEstimator2.png)


# Advanced users
Advanced users can take benefit of a couple of handy features built into the tool.
## Recomputation
* If you run the tool twice, it will look into the 'Proposed_Survey_Run_Lines' layer and if there are any entries with the text string like the value set by the user in the **LinePrefix** field, they will be deleted.  This saves the user manually clearing out the layer by hand before each run.
## Auto computation of most efficient line heading
* If you set the Primary Survey Line Heading to -1, the tool will iterate through the user-selected polygon, and find the longest axis.  It will then set the heading to this orientation.  This generally creates the most efficient line plan.
## Computation of Depth
* The tool is capable of reading the GEBCO global bathymetry database in order to estimate the depths within your polygon.  The GEBCO_2014 Grid is a continuous terrain model for ocean and land with a spatial resolution of 30 arc seconds. It is an updated version of the GEBCO_08 Grid. The file the tool reads is the **1D netCDF** version. It can be downloaded from here:

https://www.gebco.net/data_and_products/gridded_bathymetry_data/gebco_30_second_grid/

* If you do not provide a valid filename, the tool cannot compute the depths for you
* The file will be called something like **GEBCO_2014_1D.nc**, and is about 2 gigabytes in size.
* Once you have downloaded the file, place it into a folder such as c:\projects\gebco, and provide the full path and filename into the text box of the dialog.  The tool can then open the file, and read the depths from the file.
The tool will not attempt to read the entire GEBCO database.  It will compute the bounding box of the user selected polygon, and extract the GEBCO bathymetry requied for the estimation process.  The extracted bathymetry will be added to a SSDM-compliant layer for you, so you can better understand the survey area under consideration.




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
