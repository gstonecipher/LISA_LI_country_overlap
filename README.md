# LISA LI country Overlap
Calculating the overlap of linear infrastructure with important biodiversity areas in 28 Asian countries

This script takes an analysis that was conducted at the Asia-wide scale and replicates it at the country level to make the information more accessible to country-level decision-makers. The script accomplishes two general categories of tasks: 1) Clip input layers to a country extent and write new feature layers; and 2) Conduct analyses regarding layer overlap and create data tables containing summary information. For part 1, the input layers include proposed linear infrastructure and protected areas (both vector datasets), as well as core biodiversity areas at the 70, 80, and 90th percentiles (raster datasets). Each of these datasets is clipped to the country level, and in the case of the raster layers, converted to a shapefile. These feature layers are all then saved to a newly created sub-folder, making it easy to access the data required for map-making. For part 2, four main analyses are run: calculating the percentage of core biodiversity layers at each cutoff that are designated as a protected area; calculating the total length of each mode of LI in the country, calculating the total length of each mode of LI that intersected with core biodiversity areas, and calculated the total area of LI, with a 25 km buffer, that intersects with core biodiversity areas for each mode. The results of these analyses are exported as CSVs.
