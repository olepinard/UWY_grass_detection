import os
import json
import planet
import asyncio
import requests
from requests.auth import HTTPBasicAuth
# import geopandas as gpd
# import shapely
PLANET_API_KEY = 'PLAKf0a992c04a964bcdbf3f09605f740fd5'
auth = HTTPBasicAuth(PLANET_API_KEY, '')

# def parse_shapefile(filename):
#     # TODO: Switch from geopandas to something that doesn't require Fiona (and by proxy, GDAL) for shapefile parsing
#     # e.g. PyShp + PyProj
#     shapefile = gpd.read_file(filename)
#
#     # All geoms used in api requests must be in epsg:4326
#     if shapefile.crs != "epsg:4326":
#         shapefile = shapefile.to_crs("epsg:4326")
#
#     polys = []
#     for geom in shapefile["geometry"].values:
#         if geom:
#             if geom.geom_type == 'MultiPolygon':
#                 # Split any multipolygons
#                 polys.extend(list(geom))
#             elif geom.geom_type == 'Polygon':
#                 polys.append(geom)
#             else:
#                 raise GeometryError("Invalid geometry type: " + geom.geom_type)
#         else:
#             print("WARNING: Found null geometry in {}".format(filename))
#
#     return list(shapely.geometry.mapping(p) for p in polys)

# Read a geojson file as a list of geometries
def parse_geojson(filename):
    geoms = {}
    features = json.load(open(filename))
    if "type" in features and features["type"] == "FeatureCollection":
        for f in features["features"]:
            geoms[f["properties"]["Name"]] = f["geometry"]
    elif "type" in features and features["type"] == "Feature":
        geoms[features["properties"]["Name"]] = [features["geometry"]]
    else:
        geoms = [features]

    return geoms

def create_request(aoi,plot,basemap):
    order_params = {
        "name": plot,
        "source_type": "basemaps",
        "order_type": "partial",
        "products": [
            {
                "mosaic_name": basemap,
                "geometry": aoi
            }
        ],
        "tools": [
            {"merge": {}},
            {"clip": {}},
            {"bandmath": {
                "b1": "b1",
                "b2": "b2",
                "b3": "b3",
                "b4": 'b4',
                "b5": "(b4-b3)/(b4+b3)*1000+1000",
                "pixel_type": "16U"
                }
            }
        ]
    }

    return order_params

def get_basemap_names():

    #global_monthly = ['global_monthly_2020_01_mosaic', 'global_monthly_2020_02_mosaic', 'global_monthly_2020_03_mosaic', 'global_monthly_2020_04_mosaic', 'global_monthly_2020_05_mosaic', 'global_monthly_2020_06_mosaic', 'global_monthly_2020_07_mosaic', 'global_monthly_2020_08_mosaic', 'global_monthly_2020_09_mosaic', 'global_monthly_2020_10_mosaic', 'global_monthly_2020_11_mosaic', 'global_monthly_2020_12_mosaic', 'global_monthly_2021_01_mosaic', 'global_monthly_2021_02_mosaic', 'global_monthly_2021_03_mosaic', 'global_monthly_2021_04_mosaic', 'global_monthly_2021_05_mosaic', 'global_monthly_2021_06_mosaic', 'global_monthly_2021_07_mosaic', 'global_monthly_2021_08_mosaic', 'global_monthly_2021_09_mosaic', 'global_monthly_2021_10_mosaic', 'global_monthly_2021_11_mosaic', 'global_monthly_2021_12_mosaic', 'global_monthly_2022_01_mosaic', 'global_monthly_2022_02_mosaic', 'global_monthly_2022_03_mosaic', 'global_monthly_2022_04_mosaic', 'global_monthly_2022_05_mosaic', 'global_monthly_2022_06_mosaic', 'global_monthly_2022_07_mosaic', 'global_monthly_2022_08_mosaic', 'global_monthly_2022_09_mosaic', 'global_monthly_2022_10_mosaic', 'global_monthly_2022_11_mosaic', 'global_monthly_2022_12_mosaic', 'global_monthly_2023_01_mosaic', 'global_monthly_2023_02_mosaic', 'global_monthly_2023_03_mosaic', 'global_monthly_2023_04_mosaic']
    global_monthly = [] 
    cont = True
    BASEMAP_API_URL = 'https://api.planet.com/basemaps/v1/mosaics'
    basemapServiceResponse = requests.get(url=BASEMAP_API_URL, auth=auth)

    while cont:
        basemaps = json.loads(basemapServiceResponse.text)
        mosaics = basemaps['mosaics']
        names = [feature['name'] for feature in mosaics]
        print(names[0])
        for name in names:
            global_monthly.append(name)
            # if "global_monthly" == name[:14]:
            #     global_monthly.append(name)
        if "_next" not in basemaps["_links"]:
            cont = False
        else:
            next_url = basemaps['_links']['_next']
            basemapServiceResponse = requests.get(url=next_url, auth=auth)

    return global_monthly

async def create_and_download(client,order,directory):
    directory = directory+'/'+order['name']+'/'+order['products'][0]['mosaic_name']


    """Make an order, wait for completion, download files as a single task."""
    with planet.reporting.StateBar(state='creating') as reporter:
        order = await client.create_order(order)
        reporter.update(state='created', order_id=order['id'])
        await client.wait(order['id'], callback=reporter.update_state)
    await client.download_order(order['id'], directory, progress_bar=True)



async def main(name):

    file_name = "./JoCoAOI.geojson"
    dir = "JoCoAOI"
    if not os.path.exists(dir):
       os.mkdir(dir)
    basemaps = get_basemap_names()
    print(len(basemaps))
    print(basemaps)
    plots = parse_geojson(file_name)
    order_request = []
    for plot in plots:
        directory = dir + '/' + plot
        if not os.path.exists(directory):
            os.mkdir(directory)
            print(directory + " now exists")
        else:
            print(directory + " already exists")

        for basemap in basemaps:
            directory = dir + '/' + plot + '/' + basemap
            if not os.path.exists(directory):
                os.mkdir(directory)
                print(directory + " now exists")
            else:
                print(directory + " already exists")

            order_request.append(create_request(plots[plot],plot,basemap))

    async with planet.Session() as sess:
        client = sess.client('orders')

        await asyncio.gather(*[create_and_download(client,order,dir) for order in order_request])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main("YAS"))

