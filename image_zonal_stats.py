import rasterio
from rasterstats import zonal_stats
import geopandas as gpd
import glob

def calculate_zonal_stats(tiff_list, geojson, folder):
    # Load the polygons from the geojson
    polygons_gdf = gpd.read_file(geojson)
    tiff_list.sort()
    for tiff in tiff_list:
        # Open the GeoTIFF file
        with rasterio.open(tiff) as src:
            bands = ['blue','green','red','NIR', 'NDVI']
            if src.count > 1:
                for i in range(src.count-1):
                    affine = src.transform
                    array = src.read(i+1)

                    # Calculate the zonal statistics for the current GeoTIFF file
                    stats = zonal_stats(polygons_gdf, array, affine=affine, stats='mean', nodata=-999)
                    # Add the statistics to the GeoDataFrame
                    polygons_gdf[tiff.split('\\')[-1].split('_')[6]+"_"+bands[i]] = [x['mean'] for x in stats]
            else:
                affine = src.transform
                array = src.read(1)

                # Calculate the zonal statistics for the current GeoTIFF file
                stats = zonal_stats(polygons_gdf, array, affine=affine, stats='mean', nodata=-999)
                # Add the statistics to the GeoDataFrame
                polygons_gdf[tiff.split('\\')[-1].split('.')[0]] = [x['mean'] for x in stats]


    # Save the result as a new geojson file
    polygons_gdf.to_file(folder+'\\'+geojson.split('\\')[-1].split('.')[0]+"_zs.geojson", driver='GeoJSON')
    print(folder+'\\'+geojson.split('\\')[-1].split('.')[0]+"_zs.geojson")

if __name__ == "__main__":
    # List of GeoTIFF files
    #Directory where all of the image folders are located
    folders = glob.glob("JoCoAOI/*")

    for folder in folders:
        #This will look for and find all of the necissary image files and store them in geotiff_filenames
        geotiff_filenames = glob.glob(folder + "/*/*/*/*mosaic_merge_clip_bandmath.tif")
        #For DEM
        #geotiff_filenames = glob.glob(folder + "/*.tif")
        if len(geotiff_filenames) == 0:
            geotiff_filenames = glob.glob(folder + "/*/*/*/*mosaic_clip_bandmath.tif")

        # Have the geojson in each AOI subfolder so that it can create the geojson with zonal stats
        geojson_file = glob.glob(folder+'\\*.geojson')

        calculate_zonal_stats(geotiff_filenames, geojson_file[0], folder)


