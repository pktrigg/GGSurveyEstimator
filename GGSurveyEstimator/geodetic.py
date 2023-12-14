#!/usr/bin/python
#
# ---------------------------------------------------------------------
# |																	 |
# |	geodetic.cc -  a collection of geodetic functions			   |
# |	Paul Kennedy May 2016										   |
# |	Jim Leven  - Dec 99											 |
# |																	 |
# | originally from:													|
# | http://wegener.mechanik.tu-darmstadt.de/GMT-Help/Archiv/att-8710/Geodetic_py |
# |ftp://pdsimage2.wr.usgs.gov/pub/pigpen/Python/Geodetic_py.py		|
# |																	 |
# ---------------------------------------------------------------------
#
#
# ------------------------------------------------------------------------------
# | Algrothims from Geocentric Datum of Australia Technical Manual			|
# | 												|
# | http://www.anzlic.org.au/icsm/gdatum/chapter4.html					|
# | 												|
# | This page last updated 11 May 1999 								|
# | 												|
# | Computations on the Ellipsoid									|
# | 												|
# | There are a number of formulae that are available		   		|
# | to calculate accurate geodetic positions, 							|
# | azimuths and distances on the ellipsoid.							|
# | 												|
# | Vincenty's formulae (Vincenty, 1975) may be used 						|
# | for lines ranging from a few cm to nearly 20,000 km, 					|
# | with millimetre accuracy. 									|
# | The formulae have been extensively tested 								|
# | for the Australian region, by comparison with results	   		|
# | from other formulae (Rainsford, 1955 & Sodano, 1965). 					|
# |												|
# | * Inverse problem: azimuth and distance from known 					|
# |			latitudes and longitudes 					|
# | * Direct problem: Latitude and longitude from known 					|
# |			position, azimuth and distance. 				|
# | * Sample data 										|
# | * Excel spreadsheet 											|
# | 												|
# | Vincenty's Inverse formulae										|
# | Given: latitude and longitude of two points				 		|
# |			(latitude1, longitude1 and latitude2, longitude2), 	|
# | Calculate: the ellipsoidal distance (s) and 						|
# | forward and reverse azimuths between the points (alpha1Tp2, alpha21).	|
# |											|
# ------------------------------------------------------------------------------

import math
import numpy as np

def medfilt (x, k):
	"""Apply a length-k median filter to a 1D array x.
	Boundaries are extended by repeating endpoints.
	"""
	assert k % 2 == 1, "Median filter length must be odd."
	assert x.ndim == 1, "Input must be one-dimensional."
	k2 = (k - 1) // 2
	y = np.zeros ((len (x), k), dtype=x.dtype)
	y[:,k2] = x
	for i in range (k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i+1)] = x[j:]
		y[-j:,-(i+1)] = x[-1]
	return np.median (y, axis=1)

# from: http://mathforum.org/library/drmath/view/62034.html
def calculateRangeBearingFromGridPosition(easting1, northing1, easting2, northing2):
	"""given 2 east, north, pairs, compute the range and bearing"""

	dx = easting2-easting1
	dy = northing2-northing1

	bearing = 90 - (180/math.pi)*math.atan2(northing2-northing1, easting2-easting1)
	return (math.sqrt((dx*dx)+(dy*dy)), bearing)


#def CalcGridCoord(easting, northing, rng, bearing):
def calculateGridPositionFromRangeBearing(easting, northing, rng, bearing):
	x2 = easting + (math.cos(math.radians(270 - bearing)) * rng)
	y2 = northing + (math.sin(math.radians(270 - bearing)) * rng)

	#test calc....
	#r,b = calculateRangeBearingFromGridPosition(easting1, northing1, x2, y 2)

	return (x2, y2)

# taken frm http://gis.stackexchange.com/questions/76077/how-to-create-points-based-on-the-distance-and-bearing-from-a-survey-point
def xxxcalculateGridPositionFromRangeBearing(easting, northing, distance, bearing):
	"""given an east, north, range and bearing, compute a new coordinate on the grid"""
	point =   (easting, northing)
	angle =   90 - bearing
	angle =   math.radians(angle)

	# polar coordinates
	dist_x = distance * math.cos(angle)
	dist_y = distance * math.sin(angle)

	xfinal = point[0] + dist_x
	yfinal = point[1] + dist_y

#x1 = x0 + distance*cos(bearing)
#y1 = y0 + distance*sin(bearing)


	# direction cosines
#	bearing = math.radians(bearing)
#	cosa = math.cos(angle)
#	cosb = math.cos(bearing)
#	xfinal = point[0] + (distance * cosa)
#	yfinal = point[1] + (distance * cosb)

	return [xfinal, yfinal]

# polar coordinates

#point = (-1004.00, 635.00)
#distance = 160
#bearing =  103
#angle =     90 - bearing
#bearing = math.radians(bearing)
#angle =   math.radians(angle)
#dist_x, dist_y = \
#    (distance * math.cos(angle), distance * math.sin(angle))
#print dist_x, dist_y
#(155.89921036563763, -35.992168695018407)
##xfinal, yfinal = (point[0] + dist_x, point[1] + dist_y)
#print xfinal, yfinal
#(-848.1007896343624, 599.00783130498155)

# direction cosines

#cosa = math.cos(angle)
#cosb = math.cos(bearing)
#xfinal, yfinal = \
#    (point[0] +(distance * cosa), point[1]+(distance * cosb))
#print xfinal, yfinal

def normalize360(bearing):
	orientation = bearing % 360

	if orientation < 0:
		orientation += 360

	return orientation

def calculateRangeBearingFromGeographicals2(longitude1, latitude1,  longitude2,  latitude2 ) :
	# WGS84
	a = 6378137.0
	b = 6356752.3142
	f = (a-b)/a

	# lembda is longitude
	# phi is latitude
	phi1 = math.radians(latitude1)
	lembda1 = math.radians(longitude1)
	phi2 = math.radians(latitude2)
	lembda2 = math.radians(longitude2)
	s, brg, brg2 = vinc_dist(  f,  a,  phi1,  lembda1,  phi2,  lembda2 )

	# print ("Long1", longitude1)
	# print ("Lat1", latitude1)

	# print ("Long2", longitude2)
	# print ("Lat2", latitude2)
	# print ("s", s)
	# phi1 = -(( 3.7203 / 60. + 57) / 60. + 37 )
	# lembda1 = ( 29.5244 / 60. + 25) / 60. + 144

	# phi2 = -(( 10.1561 / 60. + 39) / 60. + 37 )
	# lembda2 = ( 35.3839 / 60. + 55) / 60. + 143
	# dist, alpha12, alpha21   = vinc_dist  ( f, a, math.radians(phi1), math.radians(lembda1), math.radians(phi2),  math.radians(lembda2) )
	# print ("XXX", dist)

	return s, brg

def vinc_dist(  f,  a,  phi1,  lembda1,  phi2,  lembda2 ) :
		"""
		Returns the distance between two geographic points on the ellipsoid
		and the forward and reverse azimuths between these points.
		lats, longs and azimuths are in radians, distance in metres
		Returns ( s, alpha12,  alpha21 ) as a tuple
		"""

		if (abs( phi2 - phi1 ) < 1e-8) and ( abs( lembda2 - lembda1) < 1e-8 ) :
		  return 0.0, 0.0, 0.0

		two_pi = 2.0*math.pi

		b = a * (1.0 - f)

		TanU1 = (1-f) * math.tan( phi1 )
		TanU2 = (1-f) * math.tan( phi2 )

		U1 = math.atan(TanU1)
		U2 = math.atan(TanU2)

		lembda = lembda2 - lembda1
		last_lembda = -4000000.0				# an impossibe value
		omega = lembda

		# Iterate the following equations,
		#  until there is no significant change in lembda

		while ( last_lembda < -3000000.0 or lembda != 0 and abs( (last_lembda - lembda)/lembda) > 1.0e-9 ) :

		  sqr_sin_sigma = pow( math.cos(U2) * math.sin(lembda), 2) + \
				pow( (math.cos(U1) * math.sin(U2) - \
				math.sin(U1) *  math.cos(U2) * math.cos(lembda) ), 2 )

		  Sin_sigma = math.sqrt( sqr_sin_sigma )

		  Cos_sigma = math.sin(U1) * math.sin(U2) + math.cos(U1) * math.cos(U2) * math.cos(lembda)

		  sigma = math.atan2( Sin_sigma, Cos_sigma )

		  Sin_alpha = math.cos(U1) * math.cos(U2) * math.sin(lembda) / math.sin(sigma)
		  alpha = math.asin( Sin_alpha )

		  Cos2sigma_m = math.cos(sigma) - (2 * math.sin(U1) * math.sin(U2) / pow(math.cos(alpha), 2) )

		  C = (f/16) * pow(math.cos(alpha), 2) * (4 + f * (4 - 3 * pow(math.cos(alpha), 2)))

		  last_lembda = lembda

		  lembda = omega + (1-C) * f * math.sin(alpha) * (sigma + C * math.sin(sigma) * \
				(Cos2sigma_m + C * math.cos(sigma) * (-1 + 2 * pow(Cos2sigma_m, 2) )))


		u2 = pow(math.cos(alpha),2) * (a*a-b*b) / (b*b)

		A = 1 + (u2/16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))

		B = (u2/1024) * (256 + u2 * (-128+ u2 * (74 - 47 * u2)))

		delta_sigma = B * Sin_sigma * (Cos2sigma_m + (B/4) * \
				(Cos_sigma * (-1 + 2 * pow(Cos2sigma_m, 2) ) - \
				(B/6) * Cos2sigma_m * (-3 + 4 * sqr_sin_sigma) * \
				(-3 + 4 * pow(Cos2sigma_m,2 ) )))

		s = b * A * (sigma - delta_sigma)

		alpha12 = math.atan2( (math.cos(U2) * math.sin(lembda)), \
				(math.cos(U1) * math.sin(U2) - math.sin(U1) * math.cos(U2) * math.cos(lembda)))

		alpha21 = math.atan2( (math.cos(U1) * math.sin(lembda)), \
				(-math.sin(U1) * math.cos(U2) + math.cos(U1) * math.sin(U2) * math.cos(lembda)))

		if ( alpha12 < 0.0 ) :
				alpha12 =  alpha12 + two_pi
		if ( alpha12 > two_pi ) :
				alpha12 = alpha12 - two_pi

		alpha21 = alpha21 + two_pi / 2.0
		if ( alpha21 < 0.0 ) :
				alpha21 = alpha21 + two_pi
		if ( alpha21 > two_pi ) :
				alpha21 = alpha21 - two_pi

		return s, alpha12,  alpha21

   # END of Vincenty's Inverse formulae

def calculateRangeBearingFromGeographicals(longitude1, latitude1,  longitude2,  latitude2 ) :
		"""
		Returns s, the distance between two geographic points on the ellipsoid
		and alpha1, alpha2, the forward and reverse azimuths between these points.
		lats, longs and azimuths are in decimal degrees, distance in metres

		Returns ( s, alpha1Tp2,  alpha21 ) as a tuple
		"""
		a = 6378137.0
		b = 6356752.3142
		f = (a-b)/a

		# f = 1.0 / 298.257223563		# WGS84 1.5731303511168036253577771970004e-7
		# a = 6378137.0 			# metres

		if (abs( latitude2 - latitude1 ) < 1e-8) and ( abs( longitude2 - longitude1) < 1e-8 ) :
				return 0.0, 0.0, 0.0

		piD4   = math.atan( 1.0 )
		two_pi = piD4 * 8.0

		latitude1	= math.radians(latitude1)
		longitude1 = math.radians(longitude1)
		latitude2	= math.radians(latitude2)
		longitude2 = math.radians(longitude2)

		# latitude1	= latitude1 * piD4 / 45.0
		# longitude1 = longitude1 * piD4 / 45.0		# unfortunately lambda is a key word!
		# latitude2	= latitude2 * piD4 / 45.0
		# longitude2 = longitude2 * piD4 / 45.0

		b = a * (1.0 - f)

		TanU1 = (1-f) * math.tan( latitude1 )
		TanU2 = (1-f) * math.tan( latitude2 )

		U1 = math.atan(TanU1)
		U2 = math.atan(TanU2)

		lembda = longitude2 - longitude1
		last_lembda = -4000000.0		# an impossibe value
		omega = lembda

		# Iterate the following equations,
		#  until there is no significant change in lembda

		while ( last_lembda < -3000000.0 or lembda != 0 and abs( (last_lembda - lembda)/lembda) > 1.0e-9 ) :

				sqr_sin_sigma = pow( math.cos(U2) * math.sin(lembda), 2) + \
						pow( (math.cos(U1) * math.sin(U2) - \
						math.sin(U1) *  math.cos(U2) * math.cos(lembda) ), 2 )

				Sin_sigma = math.sqrt( sqr_sin_sigma )

				Cos_sigma = math.sin(U1) * math.sin(U2) + math.cos(U1) * math.cos(U2) * math.cos(lembda)

				sigma = math.atan2( Sin_sigma, Cos_sigma )

				Sin_alpha = math.cos(U1) * math.cos(U2) * math.sin(lembda) / math.sin(sigma)
				alpha = math.asin( Sin_alpha )

				Cos2sigma_m = math.cos(sigma) - (2 * math.sin(U1) * math.sin(U2) / pow(math.cos(alpha), 2) )

				C = (f/16) * pow(math.cos(alpha), 2) * (4 + f * (4 - 3 * pow(math.cos(alpha), 2)))

				last_lembda = lembda

				lembda = omega + (1-C) * f * math.sin(alpha) * (sigma + C * math.sin(sigma) * \
						(Cos2sigma_m + C * math.cos(sigma) * (-1 + 2 * pow(Cos2sigma_m, 2) )))

		u2 = pow(math.cos(alpha),2) * (a*a-b*b) / (b*b)

		A = 1 + (u2/16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))

		B = (u2/1024) * (256 + u2 * (-128+ u2 * (74 - 47 * u2)))

		delta_sigma = B * Sin_sigma * (Cos2sigma_m + (B/4) * \
				(Cos_sigma * (-1 + 2 * pow(Cos2sigma_m, 2) ) - \
				(B/6) * Cos2sigma_m * (-3 + 4 * sqr_sin_sigma) * \
				(-3 + 4 * pow(Cos2sigma_m,2 ) )))

		s = b * A * (sigma - delta_sigma)

		alpha1Tp2 = math.atan2( (math.cos(U2) * math.sin(lembda)), \
				(math.cos(U1) * math.sin(U2) - math.sin(U1) * math.cos(U2) * math.cos(lembda)))

		alpha21 = math.atan2( (math.cos(U1) * math.sin(lembda)), \
				(-math.sin(U1) * math.cos(U2) + math.cos(U1) * math.sin(U2) * math.cos(lembda)))

		if ( alpha1Tp2 < 0.0 ) :
				alpha1Tp2 =  alpha1Tp2 + two_pi
		if ( alpha1Tp2 > two_pi ) :
				alpha1Tp2 = alpha1Tp2 - two_pi

		alpha21 = alpha21 + two_pi / 2.0
		if ( alpha21 < 0.0 ) :
				alpha21 = alpha21 + two_pi
		if ( alpha21 > two_pi ) :
				alpha21 = alpha21 - two_pi

		alpha1Tp2	= alpha1Tp2	* 45.0 / piD4
		alpha21	= alpha21	* 45.0 / piD4
		return s, alpha1Tp2,  alpha21

   # END of Vincenty's Inverse formulae


#-------------------------------------------------------------------------------
# Vincenty's Direct formulae							|
# Given: latitude and longitude of a point (latitude1, longitude1) and 			|
# the geodetic azimuth (alpha1Tp2) 						|
# and ellipsoidal distance in metres (s) to a second point,			|
# 										|
# Calculate: the latitude and longitude of the second point (latitude2, longitude2) 	|
# and the reverse azimuth (alpha21).						|
# 										|
#-------------------------------------------------------------------------------

def calculateCoordinateFromRangeBearing(X, Y, Range, Bearing, isGeographic):
	if isGeographic:
		Y1, X1, s = calculateGeographicalPositionFromRangeBearing(Y, X, Bearing, Range )
		return X1, Y1
	else:
		X1, Y1 = calculateGridPositionFromRangeBearing(X, Y, Range, Bearing)
		return X1, Y1

def calculateRangeBearingFromCoordinates(X1, Y1, X2, Y2, isGeographic):
	if isGeographic:
		rng, bearing = calculateRangeBearingFromGeographicals2(X1, Y1, X2, Y2 )
		# print ("ff", rng, X1, Y1, X2, Y2)
		return rng, math.degrees(bearing)
	else:
		rng, bearing = calculateRangeBearingFromGridPosition(X1, Y1, X2, Y2)
		return rng, bearing

def calculateGeographicalPositionFromRangeBearing(latitude1, longitude1, alpha1To2, s ) :
		"""
		Returns the lat and long of projected point and reverse azimuth
		given a reference point and a distance and azimuth to project.
		lats, longs and azimuths are passed in decimal degrees

		Returns ( latitude2,  longitude2,  alpha2To1 ) as a tuple
		"""
		f = 1.0 / 298.257223563		# WGS84
		a = 6378137.0 			# metres

		piD4 = math.atan( 1.0 )
		two_pi = piD4 * 8.0

		if s == 0:
			return latitude1,  longitude1,  0.0

		latitude1	= latitude1	* piD4 / 45.0
		longitude1 = longitude1 * piD4 / 45.0
		alpha1To2 = alpha1To2 * piD4 / 45.0
		if ( alpha1To2 < 0.0 ) :
				alpha1To2 = alpha1To2 + two_pi
		if ( alpha1To2 > two_pi ) :
				alpha1To2 = alpha1To2 - two_pi

		b = a * (1.0 - f)

		TanU1 = (1-f) * math.tan(latitude1)
		U1 = math.atan( TanU1 )
		sigma1 = math.atan2( TanU1, math.cos(alpha1To2) )
		Sinalpha = math.cos(U1) * math.sin(alpha1To2)
		cosalpha_sq = 1.0 - Sinalpha * Sinalpha

		u2 = cosalpha_sq * (a * a - b * b ) / (b * b)
		A = 1.0 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * \
				(320 - 175 * u2) ) )
		B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2) ) )

		# Starting with the approximation
		sigma = (s / (b * A))

		last_sigma = 2.0 * sigma + 2.0	# something impossible

		# Iterate the following three equations
		#  until there is no significant change in sigma

		# two_sigma_m , delta_sigma
		while ( abs( (last_sigma - sigma) / sigma) > 1.0e-9 ) :
				two_sigma_m = 2 * sigma1 + sigma

				delta_sigma = B * math.sin(sigma) * ( math.cos(two_sigma_m) \
						+ (B/4) * (math.cos(sigma) * \
						(-1 + 2 * math.pow( math.cos(two_sigma_m), 2 ) -  \
						(B/6) * math.cos(two_sigma_m) * \
						(-3 + 4 * math.pow(math.sin(sigma), 2 )) *  \
						(-3 + 4 * math.pow( math.cos (two_sigma_m), 2 ))))) \

				last_sigma = sigma
				sigma = (s / (b * A)) + delta_sigma

		latitude2 = math.atan2 ( (math.sin(U1) * math.cos(sigma) + math.cos(U1) * math.sin(sigma) * math.cos(alpha1To2) ), \
				((1-f) * math.sqrt( math.pow(Sinalpha, 2) +  \
				pow(math.sin(U1) * math.sin(sigma) - math.cos(U1) * math.cos(sigma) * math.cos(alpha1To2), 2))))

		lembda = math.atan2( (math.sin(sigma) * math.sin(alpha1To2 )), (math.cos(U1) * math.cos(sigma) -  \
				math.sin(U1) *  math.sin(sigma) * math.cos(alpha1To2)))

		C = (f/16) * cosalpha_sq * (4 + f * (4 - 3 * cosalpha_sq ))

		omega = lembda - (1-C) * f * Sinalpha *  \
				(sigma + C * math.sin(sigma) * (math.cos(two_sigma_m) + \
				C * math.cos(sigma) * (-1 + 2 * math.pow(math.cos(two_sigma_m),2) )))

		longitude2 = longitude1 + omega

		alpha21 = math.atan2 ( Sinalpha, (-math.sin(U1) * math.sin(sigma) +  \
				math.cos(U1) * math.cos(sigma) * math.cos(alpha1To2)))

		alpha21 = alpha21 + two_pi / 2.0
		if ( alpha21 < 0.0 ) :
				alpha21 = alpha21 + two_pi
		if ( alpha21 > two_pi ) :
				alpha21 = alpha21 - two_pi

		latitude2	   = latitude2	   * 45.0 / piD4
		longitude2	= longitude2	* 45.0 / piD4
		alpha21	= alpha21	* 45.0 / piD4

		return latitude2,  longitude2,  alpha21

  # END of Vincenty's Direct formulae

#--------------------------------------------------------------------------
# Notes:
#
# * "The inverse formulae may give no solution over a line
# 	between two nearly antipodal points. This will occur when
# 	lembda ... is greater than pi in absolute value". (Vincenty, 1975)
#
# * In Vincenty (1975) L is used for the difference in longitude,
# 	however for consistency with other formulae in this Manual,
# 	omega is used here.
#
# * Variables specific to Vincenty's formulae are shown below,
# 	others common throughout the manual are shown in the Glossary.
#
#
# alpha = Azimuth of the geodesic at the equator
# U = Reduced latitude
# lembda = Difference in longitude on an auxiliary sphere (longitude1 & longitude2
# 		are the geodetic longitudes of points 1 & 2)
# sigma = Angular distance on a sphere, from point 1 to point 2
# sigma1 = Angular distance on a sphere, from the equator to point 1
# sigma2 = Angular distance on a sphere, from the equator to point 2
# sigma_m = Angular distance on a sphere, from the equator to the
# 		midpoint of the line from point 1 to point 2
# u, A, B, C = Internal variables
#
#
# Sample Data
#
# Flinders Peak
# -37 57'03.72030"
# 144 25'29.52440"
# Buninyong
# -37 39'10.15610"
# 143 55'35.38390"
# Ellipsoidal Distance
# 54,972.271 m
#
# Forward Azimuth
# 306 52'05.37"
#
# Reverse Azimuth
# 127 10'25.07"
#
#
#*******************************************************************

# Test driver

if __name__ == "__main__" :

		f = 1.0 / 298.257223563		# WGS84
		a = 6378137.0 			# metres

		print  ("\n Ellipsoidal major axis =  %12.3f metres\n" % ( a ))
		print  ("\n Inverse flattening	 =  %15.9f\n" % ( 1.0/f ))

		print ("\n Test Flinders Peak to Buninyon")
		print ("\n ****************************** \n")
		latitude1 = -(( 3.7203 / 60. + 57) / 60. + 37 )
		longitude1 = ( 29.5244 / 60. + 25) / 60. + 144
		print ("Flinders Peak = %12.6f, %13.6f \n" % ( latitude1, longitude1 ))
		deg = int(latitude1)
		min = int(abs( ( latitude1 - deg) * 60.0 ))
		sec = abs(latitude1 * 3600 - deg * 3600) - min * 60
		print (" Flinders Peak =   %3i\xF8%3i\' %6.3f\",  " % ( deg, min, sec ),)
		deg = int(longitude1)
		min = int(abs( ( longitude1 - deg) * 60.0 ))
		sec = abs(longitude1 * 3600 - deg * 3600) - min * 60
		print (" %3i\xF8%3i\' %6.3f\" \n" % ( deg, min, sec ))

		latitude2 = -(( 10.1561 / 60. + 39) / 60. + 37 )
		longitude2 = ( 35.3839 / 60. + 55) / 60. + 143
		print ("\n Buninyon	  = %12.6f, %13.6f \n" % ( latitude2, longitude2 ))

		deg = int(latitude2)
		min = int(abs( ( latitude2 - deg) * 60.0 ))
		sec = abs(latitude2 * 3600 - deg * 3600) - min * 60
		print (" Buninyon	  =   %3i\xF8%3i\' %6.3f\",  " % ( deg, min, sec ),)
		deg = int(longitude2)
		min = int(abs( ( longitude2 - deg) * 60.0 ))
		sec = abs(longitude2 * 3600 - deg * 3600) - min * 60
		print (" %3i\xF8%3i\' %6.3f\" \n" % ( deg, min, sec ))

		dist, alpha1Tp2, alpha21   = vinc_dist  ( f, a, latitude1, longitude1, latitude2,  longitude2 )

		print ("\n Ellipsoidal Distance = %15.3f metres\n			should be		 54972.271 m\n" % ( dist ))
		print ("\n Forward and back azimuths = %15.6f, %15.6f \n" % ( alpha1Tp2, alpha21 ))
		deg = int(alpha1Tp2)
		min = int( abs(( alpha1Tp2 - deg) * 60.0 ) )
		sec = abs(alpha1Tp2 * 3600 - deg * 3600) - min * 60
		print (" Forward azimuth = %3i\xF8%3i\' %6.3f\"\n" % ( deg, min, sec ))
		deg = int(alpha21)
		min = int(abs( ( alpha21 - deg) * 60.0 ))
		sec = abs(alpha21 * 3600 - deg * 3600) - min * 60
		print (" Reverse azimuth = %3i\xF8%3i\' %6.3f\"\n" % ( deg, min, sec ))


		# Test the direct function */
		latitude1 = -(( 3.7203 / 60. + 57) / 60. + 37 )
		longitude1 = ( 29.5244 / 60. + 25) / 60. + 144
		dist = 54972.271
		alpha1Tp2 = ( 5.37 / 60. + 52) / 60. + 306
		latitude2 = longitude2 = 0.0
		alpha21 = 0.0

		latitude2, longitude2, alpha21 = vincentyDirect (latitude1, longitude1, alpha1Tp2, dist )

		print ("\n Projected point =%11.6f, %13.6f \n" % ( latitude2, longitude2 ))
		deg = int(latitude2)
		min = int(abs( ( latitude2 - deg) * 60.0 ))
		sec = abs( latitude2 * 3600 - deg * 3600) - min * 60
		print (" Projected Point = %3i\xF8%3i\' %6.3f\", " % ( deg, min, sec ),)
		deg = int(longitude2)
		min = int(abs( ( longitude2 - deg) * 60.0 ))
		sec = abs(longitude2 * 3600 - deg * 3600) - min * 60
		print ("  %3i\xF8%3i\' %6.3f\"\n" % ( deg, min, sec ))
		print (" Should be Buninyon \n" )
		print ("\n Reverse azimuth = %10.6f \n" % ( alpha21 ))
		deg = int(alpha21)
		min = int(abs( ( alpha21 - deg) * 60.0 ))
		sec = abs(alpha21 * 3600 - deg * 3600) - min * 60
		print (" Reverse azimuth = %3i\xF8%3i\' %6.3f\"\n\n" % ( deg, min, sec ))

#*******************************************************************

def est_dist(  latitude1,  longitude1,  latitude2,  longitude2 ) :
		"""

		Returns an estimate of the distance between two geographic points
		This is a quick and dirty vinc_dist
		which will generally estimate the distance to within 1%
		Returns distance in metres

		"""
		f = 1.0 / 298.257223563		# WGS84
		a = 6378137.0 			# metres

		piD4   = 0.785398163397

		latitude1	= latitude1 * piD4 / 45.0
		longitude1 = longitude1 * piD4 / 45.0
		latitude2	= latitude2 * piD4 / 45.0
		longitude2 = longitude2 * piD4 / 45.0

		c = math.cos((latitude2+latitude1)/2.0)

		return math.sqrt( pow(math.fabs(latitude2-latitude1), 2) + \
				pow(math.fabs(longitude2-longitude1)*c, 2) ) * a * ( 1.0 - f + f * c )
   # END of rough estimate of the distance.######################################################################################
def degreesToMetres(degrees):
	return (degrees * (1852*60))
######################################################################################
def metresToDegrees(metres):
	return (metres / (1852*60))
######################################################################################
def rangeBearing(lat1, lon1, d, brng):
	R = 6378.1 #Radius of the Earth

	brng = math.radians(brng)
	# brng = 1.57 #Bearing is 90 degrees converted to radians.
	# d = 15 #Distance in km

	d = d / 1000.0

	#lat2  52.20444 - the lat result I'm hoping for
	#lon2  0.36056 - the long result I'm hoping for.

	lat1 = math.radians(lat1)
	lon1 = math.radians(lon1)
	# lat1 = math.radians(52.20472) #Current lat point converted to radians
	# lon1 = math.radians(0.14056) #Current long point converted to radians

	lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
		math.cos(lat1)*math.sin(d/R)*math.cos(brng))

	lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
				math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

	lat2 = math.degrees(lat2)
	lon2 = math.degrees(lon2)

	# print(lat2)
	# print(lon2)
	return (lat2, lon2)

		# private double calcBearing(IPoint p1, IPoint p2)
		# {
		#	 // get E/N distances between ref1 & ref2
		#	 var deltaE = p2.X - p1.X;
		#	 var deltaN = p2.Y - p1.Y;

		#	 // arctan gives us the bearing, just need to convert -pi..+pi to 0..360 deg
		#	 var deg = (90 - (Math.Atan2(deltaN, deltaE) / Math.PI * 180) + 360) % 360;
		#	 return deg;  // return result in degrees, no decimals
		# }

		# public double CalcRange(IPoint p1, IPoint p2)
		# {
		#	 // get E/N distances between ref1 & ref2
		#	 double deltaE = p2.X - p1.X;
		#	 double deltaN = p2.Y - p1.Y;
		#	 if ((deltaE + deltaN) == 0)
		#		 return 0;

		#	 return Math.Sqrt(deltaE * deltaE + deltaN * deltaN);
		# }
