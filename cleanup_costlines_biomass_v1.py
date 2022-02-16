#Paulina Marczak
#March 9 2020
#Merge community costpoints with associated distance script for input into bioenergy optimization
#READ THE README "...readme.docx"

import os
import time

print "Starting at:", (time.strftime('%a %H:%M:%S'))
print "Importing modules."
try:
	import archook  # The module which locates arcgis
	archook.get_arcpy()
	import arcpy
	from arcpy.sa import *
except ImportError:
	print "Import error."
try:
	import pandas as pd
except ImportError:
	print "No pandas found- must install from pip"
import csv
try:
	import re
except Import:
	print "re not imported"

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("spatial")

#set workspace
script_dir = os.path.dirname(os.path.realpath(__file__))
line_workspace= os.path.join(script_dir, "EventODcostlinesCarbonTonnes.gdb")
cutblock_workspace = os.path.join(script_dir, "BiomassCarbonTonnesBCAlbers.gdb")

#use costline workspace first
arcpy.env.workspace = line_workspace

#Build names of costlines and Harvest Centroids

#Create list to get input harvest centroids
def createList(r1, r2): 
	return list(range(r1, r2+1)) 

#Apply list to range of values (31= 2020; 81=2070)
r1, r2 = 31, 81
yearRange= createList(r1,r2)
input_list= []
extension_list= ['costlinesHarvCent', 'HarvCent', "costlinesHarvCent_point"]
for i in yearRange:
	for e in extension_list:
		entry= e+ "0" +str(i) 
		input_list.append(entry)

print input_list

final_list = []

#convert costlines to origin point
fields = ['x1','x2','y1','y2']

#Add x, y origin points to costlines
for item in input_list:
	if item.startswith("costlinesHarvCent") and "point" not in item:
		for field in fields:
			print "Adding in", field, "origin point to", item
			newfield=field
			type = "DOUBLE"
			arcpy.DeleteField_management(item, field)
			arcpy.AddField_management(item,newfield, type)

	# 	# fill in origin destination xy fields
		with arcpy.da.UpdateCursor(item, ('x1','x2','y1','y2', "SHAPE@")) as cursor:
			print "Adding in origin points to", item
			for row in cursor:
				row[0] = row[4].firstPoint.X
				row[1] = row[4].lastPoint.X
				row[2] = row[4].firstPoint.Y
				row[3] = row[4].lastPoint.Y
				cursor.updateRow(row)

	# 	#convert to point based on this origin point (costline_points)

		#convert line shp to dbf table so that you can use xy origin to reconstruct as points
		out_path= line_workspace
		out_name= item + "table"
		print "Converting to dbf table to use xy origin to reconstruct lines as points"
		arcpy.TableToTable_conversion(item, out_path, out_name)

	# 	#try to convert to point file
		
		arcpy.env.workspace= line_workspace

	# 	#convert table to points
		try:
			arcpy.env.overwriteOutput = True
			in_feature= out_name
			out_feature_class= "costlinesHarvCent_point_temp" + item.split("costlinesHarvCent")[1]
			x_coords = "x1"
			y_coords = "y1"
			z_coords = ""
			outLocation= line_workspace
			export_layer= "costlinesHarvCent_point" + item.split("costlinesHarvCent")[1]
			print "exporting", export_layer
			spRef = r"Coordinate Systems\\Projected Coordinate Systems\\Utm\\Nad 1983\\NAD 1983 BC Environment Albers.prj"
			arcpy.MakeXYEventLayer_management(in_feature, x_coords, y_coords, out_feature_class, spRef, z_coords)
			arcpy.FeatureClassToFeatureClass_conversion(out_feature_class, outLocation, 
											export_layer)
		except Exception as err:
			print(err.args[0])

	# Make a unique ID for each harvest centroid point based on 
	# #The unique ID it already has plus the year number in the filename

	#first create the empty field
	arcpy.env.workspace= cutblock_workspace

	#create a year field and make unique ID column based on year plus HarvCentID  
	if item.startswith("HarvCent"):
		print "Adding in unique ID point to", item
		newfield= "HarvCent_ID"
		newfield2= "Year"
		type = "text"
		arcpy.DeleteField_management(item, newfield)
		arcpy.DeleteField_management(item, newfield2)
		arcpy.AddField_management(item,newfield, type)
		arcpy.AddField_management(item,newfield2, type)
		year=  item.split("HarvCent")[1] + "_"
		with arcpy.da.UpdateCursor(item, "Year") as cursor:
			for row in cursor:
				year=  item.split("HarvCent")[1] + "_"
				row[0] =  year
				cursor.updateRow(row)
		rows=["HarvCent_ID", "NEAR_FID", "Year"]
		with arcpy.da.UpdateCursor(item, rows) as cursor:
			for row in cursor:
				#make unique ID based on NEAR_FID and Year
				row[0] =  str(row[2]) + str(row[1])
				row[2] = row[2].split("_")[0]
				cursor.updateRow(row)

		#get new tc instead of tc/ha field
		#need to get lat and long
		arcpy.env.overwriteOutput = True
		#arcpy.ConvertCoordinateNotation_management(in_table=item, out_featureclass=item+"_temp", x_field="", y_field="", input_coordinate_format="SHAPE", output_coordinate_format="DD_2", id_field="", spatial_reference="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision", in_coor_system="PROJCS['NAD_1983_BC_Environment_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',1000000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-126.0],PARAMETER['Standard_Parallel_1',50.0],PARAMETER['Standard_Parallel_2',58.5],PARAMETER['Latitude_Of_Origin',45.0],UNIT['Meter',1.0]]", exclude_invalid_records="INCLUDE_INVALID")
		arcpy.ConvertCoordinateNotation_management(in_table=item, out_featureclass=item + "_temp", x_field="", y_field="", input_coordinate_format="SHAPE", output_coordinate_format="DD_NUMERIC", id_field="", spatial_reference="PROJCS['NAD_1983_BC_Environment_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',1000000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-126.0],PARAMETER['Standard_Parallel_1',50.0],PARAMETER['Standard_Parallel_2',58.5],PARAMETER['Latitude_Of_Origin',45.0],UNIT['Meter',1.0]];-13239300 -8610100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision", in_coor_system="PROJCS['NAD_1983_BC_Environment_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',1000000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-126.0],PARAMETER['Standard_Parallel_1',50.0],PARAMETER['Standard_Parallel_2',58.5],PARAMETER['Latitude_Of_Origin',45.0],UNIT['Meter',1.0]]", exclude_invalid_records="INCLUDE_INVALID")
		# "x" is the pixel width. For "1 ha" GCBM runs this should be 0.001 degrees
		#delete one copy of harvest centroid
		arcpy.Delete_management(in_data=item, data_type="FeatureClass")
		#rename as original copy
		arcpy.Rename_management(item + "_temp", item)
		x = 0.001
		gcbm_earth_radius = 6378137
		gcbm_pi = 3.141592653590
		gcbm_earth_dia_per_deg = (2.0 * gcbm_pi * gcbm_earth_radius) / 360.0
		deg_to_rad_multiplier = gcbm_pi / 180.0
		pixel_length = x * gcbm_earth_dia_per_deg
		new_value_field= "SUM_tC"
		# "residue_field" is the name of the centroid residue value in the residue feature class
		expression =r'!znsums_SUM! * ({0} * {0} * math.cos(!DDLat! * {1}) * 0.0001)'.format(pixel_length, deg_to_rad_multiplier)
		# Delete and Add field ensure that the existing values are removed.
		arcpy.DeleteField_management(item, new_value_field)
		arcpy.AddField_management(item, new_value_field, "DOUBLE")
		# Execute the expression, creating a new field with corrected (absolute) residue values
		arcpy.CalculateField_management(item, new_value_field, expression, "PYTHON_9.3")

	# #pivot the transport points to do origin dest.

	arcpy.env.workspace= line_workspace

	#Appending all 1-20 ranked communities
	r1, r2 = 1, 20
	rankRange= createList(r1,r2)
	newfieldsList = []
	community_fields= ["rankx_dest",
						"rankx_length",
						"rankx_cost",
						"rankx_paved",
						"rankx_dirt",
						"rankx_rail",
						"rankx_boat",
						"rankx_trans"
						]
	#Make list of new fields to append
	for i in rankRange:
		for j in community_fields:
			newfieldsList.append(j.split("x_")[0]+ str(i) + j.split("x")[1])

	##read cursor by name
	# from https://gist.github.com/jasonbot/3100423
	def rows_as_update_dicts(cursor):
		colnames = cursor.fields
		for row in cursor:
			row_object = dict(zip(colnames, row))
			yield row_object
			cursor.updateRow([row_object[colname] for colname in colnames])

	
	# #make the length and destination columns
	if item.startswith("costlinesHarvCent") and "point" not in item:
		print "condensing and pivoting costline length and cost data for", item
		in_feat = "costlinesHarvCent_point" + item.split("Cent")[1]
		#print in_feat
		field_names = newfieldsList
		for field in newfieldsList:
		#First create the fields
			newfield = field
			if field.endswith("dest"):
				type= "TEXT"
				arcpy.DeleteField_management(in_feat, newfield)
				arcpy.AddField_management(in_feat,newfield, type)
			else:
				type = "FLOAT"
				precision = "8"
				scale = "8"
				arcpy.DeleteField_management(in_feat, newfield)
				arcpy.AddField_management(in_feat, newfield, type, precision, scale) #field is nullable
		
	# 	# fill in the new cost/ length columns with the values
	# 	# Now append existing destination ranks and total_cost for pivoting
		field_names = [f.name for f in arcpy.ListFields(in_feat)]
		print field_names

	# 	# Fill in fields with rank, name, cost, and length
		with arcpy.da.UpdateCursor(in_feat, field_names) as cursor:
			for row in rows_as_update_dicts(cursor):
				for i in range(1,21):
					if row['DestinationRank']==i:
						#strname represents the new rank_x_dest column that matches the rank within DestinationRank
						strname= "rank" + str(i) + "_dest"
						#update the corresponding rank column with the proper name column
						row[strname]= row['NAMEL']
						#fill cost column
						strname= "rank" + str(i) + "_cost"
						row[strname]= row['Total_Cost']
						#fill the length column
						strname= "rank" + str(i) + "_length"
						row[strname]= row['Total_Length']
						#fill paved
						strname= "rank" + str(i) + "_paved"
						row[strname]= row['Total_Apaved'] + row['Total_Acityspoke']
						#fill unpaved and other modes
						strname= "rank" + str(i) + "_dirt"
						row[strname]= row['Total_Aovergrown'] + row['Total_Aseasonal'] + row['Total_Aunknown'] + row['Total_Aloose']
						
						strname= "rank" + str(i) + "_rail"
						row[strname]= row['Total_Arail']

						strname= "rank" + str(i) + "_boat"
						row[strname]= row['Total_AwaterInterp'] + row['Total_Aboat'] + row['Total_Awater']

						strname= "rank" + str(i) + "_trans"
						row[strname]= row['Total_trans'] + row['Total_Wtrans']

			  cursor.updateRow(row) #fills the cost columns
			del cursor

		#reduce costline points to one point per location
		statistics_fields_list= ["_dest",
								"_cost",
								"_length",
								"_paved",
								"_dirt",
								"_rail",
								"_boat",
								"_trans"]
		statistics_fields_dissolve= []

		# #build dissolve fields
		for i in range(1,21):
			for stat in statistics_fields_list:
				stats_field=  "rank" + str(i) + stat + " MAX" + ";"
				statistics_fields_dissolve.append(stats_field)
		
		# #change last element to remove semicolon
		statistics_fields_dissolve[-1] = statistics_fields_dissolve[-1].replace(";", "")
		
		#format to the way arcpy accepts field list
		statistics_fields_dissolve= str(statistics_fields_dissolve)
		statistics_fields_dissolve = statistics_fields_dissolve.replace(",", "")
		statistics_fields_dissolve = statistics_fields_dissolve.replace("'", "")
		statistics_fields_dissolve = statistics_fields_dissolve.replace("[", "")
		statistics_fields_dissolve = statistics_fields_dissolve.replace("]", "")
		#print statistics_fields_dissolve

		arcpy.Dissolve_management(in_features= in_feat, out_feature_class= in_feat + "_dissolved", dissolve_field="OriginID", statistics_fields= statistics_fields_dissolve, multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")
		

		#fields have to be renamed
		#get list of output fields generated by dissolve, which has "MAX" in field names
		statistics_fields_in= statistics_fields_dissolve.replace(" MAX", "")
		statistics_fields_in= statistics_fields_in.replace("rank", "MAX_rank")
		statistics_fields_in= statistics_fields_in.replace(" MAX", "MAX")
		statistics_fields_in= str.split(statistics_fields_in, ";")
		print "statistics_fields_in", statistics_fields_in

		#get list of desired output field names
		#print statistics_fields_dissolve
		statistics_fields_out= statistics_fields_dissolve.replace(" MAX", "")
		statistics_fields_out= statistics_fields_out.replace(" rank", "rank")
		statistics_fields_out= str.split(statistics_fields_out, ";")
		print "statistics_fields_out", statistics_fields_out
		
		#feed lists to alter field names in each input point FC
		item1= in_feat + "_dissolved"
		overlaydict= {}

		for i in statistics_fields_in:
			target1= i
			print "i", i
			dict1= target1
			target1_part1= i.split("_")

			#get two items to match dictionary on
			target1_part2= target1_part1[1]
			target1_part3= target1_part1[2]

			print target1_part2
			print target1_part3

			for e in statistics_fields_out:
				target2= e
				print "e", e
				target2_part1= e.split("_")
				print target2_part1

				target2_part2= target2_part1[0]
				target2_part3=target2_part1[1]
				target2_part4= target2_part3.split(" ")
				target2_part5= target2_part4[0]

				print target2_part2
				print target2_part5

				if target1_part2==target2_part2 and target1_part3==target2_part5:
					dict2= target2
					overlaydict[dict1]=dict2
					print "dictionary match found for", target1, target2

		for value,event in sorted(overlaydict.items()):
			try:
				print "changing name for", value
				arcpy.AlterField_management(item1, value, event)
			except arcpy.ExecuteError:
				print arcpy.GetMessages()

			#For each rank, get a NEAR_DIST, from centroid to road distance

			#Check visually if the costline_points match up with HarvCent
			#yup looks good	
	

	#Make dictionary between costlines and Harvest Centroids
	harv_cost_dict= {}

	#match harvest centroid with costpoint if the years match
	if item.startswith("Harv"):
		target1= item
		#print "target1", target1
		year1= target1.split("Cent")[1]
		#print year1
		dict1= target1

		for item in input_list:
			if item.startswith("costlinesHarvCent_point"):
				target2= item + "_dissolved"
				print target2
				year2_pt1=target2.split("point")[1]
				#print "year2_pt1", year2_pt1
				year2_pt2=year2_pt1.split("_")[0]
				#print year2_pt2

				if year1==year2_pt2:
					dict2= target2
					harv_cost_dict[dict1]=dict2
					#print "dictionary match found for", target1, target2

	# Join respective costline_point_merged to HarvCent
	# then spatial join harv centroid to a cost point per year, if the centroid is close enough to THLB/road.
	# this process will drop a small amount of centroids. 
	# to check which harvest centroids were dropped, compare the HarvCent_ID column in the original centroid versus this output.

	#accumulate all the snapped layers
	for harv, cost in sorted(harv_cost_dict.items()):
		print "Spatially joining harvest centroid with overlaying cost information, if it exists, and dropping harvest centroids with no nearby cost information"
		joined_feat= harv + "_spatial_join"
		print harv
		print cost
		arcpy.SpatialJoin_analysis(target_features= cutblock_workspace + "\\" + harv, join_features=cost, out_feature_class= joined_feat, join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping='', match_option="INTERSECT", search_radius="20 Meters", distance_field_name="")
	
		#try near analysis; validated the output numbers are the same as what was generated by Nick
		in_Features = joined_feat

		road_workspace = os.path.join(script_dir, "Road2019cor.gdb") 

		road_list= []

		road_input_list= ["RRtrans_1",
						"Roadnet_only2_1_1splitn_1",
						"waterroutes"]
		
		search_radius = ""
		location = "LOCATION"
		angle = "NO_ANGLE"

		for road_list_item in road_input_list:
			road_path= road_workspace + "\\roadmulti3\\" + road_list_item
			road_list.append(road_path)

		#print "searching for nearest road feature"
		#You dont have to run this line because its already been done by Nick, but its here if you want to
		#arcpy.Near_analysis(in_Features, road_list, search_radius, location, angle)

		#convert newly joined feature class to dbf table so that you can use xy origin to reconstruct as points

		out_path= line_workspace
		out_name= harv + "table"
		print "converting to table to regeocode as road features"
		arcpy.TableToTable_conversion(joined_feat, out_path, out_name)

		#re-geocode to snap to road network using near feature coordinates

		#convert table to points
		arcpy.env.overwriteOutput = True
		in_feature= out_name
		out_feature_class= "costlinesHarvCent_point_temp" + in_feature.split("HarvCent")[1]
		x_coords = "NEAR_X"
		y_coords = "NEAR_Y"
		z_coords = ""
		outLocation= line_workspace
		export_layer= "HarvCent" + in_feature.split("HarvCent")[1] + "snapped"
		print "exporting newly snapped to road layer", export_layer
		spRef = r"Coordinate Systems\Projected Coordinate Systems\Utm\Nad 1983\NAD 1983 BC Environment Albers.prj"
		arcpy.MakeXYEventLayer_management(in_feature, x_coords, y_coords, out_feature_class, spRef, z_coords)
		arcpy.FeatureClassToFeatureClass_conversion(out_feature_class, outLocation, export_layer)
		#accumulate snapped layers
		print export_layer
		final_list.append(export_layer)

# Join the output files together with their unique IDs
print "final list", final_list
final_list= str(final_list)
final_list = final_list.replace("'", "")
final_list = final_list.replace("[", "")
final_list = final_list.replace("]", "")
final_list = final_list.replace(",", ";")
final_file= "Merged_Harv_Centroids_Cost_Points_Snapped_to_Roads"
arcpy.Merge_management(inputs= final_list, output=final_file, field_mappings="")
	
##export merged feature classes to .csv
arcpy.TableToTable_conversion(in_rows=final_file, out_path=script_dir, out_name="merged_harv_centroids_cost_points_snapped_to_roads.csv", where_clause="", field_mapping="", config_keyword="")
#Gap analysis with burn value 2- or 50x100 old salv mask
#visually it looks good

arcpy.CheckInExtension("spatial")
