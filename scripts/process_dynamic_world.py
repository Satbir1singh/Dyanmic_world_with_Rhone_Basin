# import ee
# import geopandas as gpd
# import json
# from shapely.geometry import mapping

# # Initialize Earth Engine
# ee.Initialize(project="ee-officialsatbir23")

# gdf = gpd.read_file("D:\GEE-project\data\BV_Rhone.shp")
# geom_json = gdf.geometry.unary_union.__geo_interface__
# roi = ee.Geometry(geom_json)

# # Define time range
# start_date = '2015-01-01'
# end_date = '2021-12-30'

# # Load and filter Sentinel-2
# s2 = (
#     ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
#     .filterBounds(roi)
#     .filterDate(start_date, end_date)
#     .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
#     .map(lambda image: image.clip(roi))
# )

# s2_image = ee.Image(s2.first())
# s2_vis_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 5000}

# # Match Dynamic World image using system:index
# image_id = s2_image.get("system:index")
# dw = (
#     ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
#     .filter(ee.Filter.eq("system:index", image_id))
#     .map(lambda image: image.clip(roi))
# )
# dw_image = ee.Image(dw.first())
# classification = dw_image.select("label")

# # Probability bands
# probability_bands = [
#     "water", "trees", "grass", "flooded_vegetation", "crops",
#     "shrub_and_scrub", "built", "bare", "snow_and_ice"
# ]
# prob_image = dw_image.select(probability_bands)

# # Compute top probability and hillshade
# top1_probability = prob_image.reduce(ee.Reducer.max())
# top1_confidence = top1_probability.multiply(100).int()
# hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)

# # Colorize classification and combine with hillshade
# dw_vis_params = {
#     "min": 0,
#     "max": 8,
#     "palette": ['#419BDF', '#397D49', '#88B053', '#7A87C6',
#                 '#E49635', '#DFC35A', '#C4281B', '#A59B8F', '#B39FE1']
# }
# rgb_image = classification.visualize(**dw_vis_params).divide(255)
# probability_hillshade = rgb_image.multiply(hillshade)

# # Export (uncomment if needed)
# # image_to_drive(
# #     image=probability_hillshade,
# #     description="Rhone_LULC_2015",
# #     folder="RhoneProject",
# #     region=roi,
# #     scale=30,
# #     max_pixels=1e10,
# # )

# # Expose to notebook
# def get_results():
#     return {
#         "s2_image": s2_image.visualize(**s2_vis_params),
#         "classification": classification.visualize(**dw_vis_params),
#         "probability_hillshade": probability_hillshade
#     }


import ee
import geopandas as gpd
from shapely.geometry import mapping

# Initialize the Earth Engine API
ee.Initialize(project="ee-officialsatbir23")

# Load your AOI shapefile
gdf = gpd.read_file("E:\D-Drive\GEE-project\data\BV_Rhone.shp")
geometry = gdf.geometry.unary_union.__geo_interface__
roi = ee.Geometry(geometry)

# Define time range
start_date = '2020-01-01'
end_date = '2021-01-01'

# Sentinel-2 Image Collection: Filter and clip to region
s2 = (
    ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filterDate(start_date, end_date)
    .filterBounds(roi)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 35))
    .map(lambda img: img.clip(roi))
)

# Create median composite
s2_image = s2.mode()
s2_vis_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 5000}

# Load Dynamic World Image Collection: Filter and clip
dw = (
    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterDate(start_date, end_date)
    .filterBounds(roi)
    .map(lambda img: img.clip(roi))
)

# Get mode classification (most frequent land class)
classification = dw.select("label").mode()

# Probability bands to calculate hillshade
probability_bands = [
    "water", "trees", "grass", "flooded_vegetation", "crops",
    "shrub_and_scrub", "built", "bare", "snow_and_ice"
]

# Get mean probability image
prob_image = dw.select(probability_bands).mean()

# Compute top class confidence and hillshade
top1_probability = prob_image.reduce(ee.Reducer.max())
top1_confidence = top1_probability.multiply(100).int()
hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)

# Color palette for land cover
dw_vis_params = {
    "min": 0,
    "max": 8,
    "palette": [
        "#419BDF",  # Water
        "#397D49",  # Trees
        "#88B053",  # Grass
        "#7A87C6",  # Flooded vegetation
        "#E49635",  # Crops
        "#DFC35A",  # Shrub and scrub
        "#C4281B",  # Built
        "#A59B8F",  # Bare
        "#B39FE1"   # Snow and ice
    ]
}

# Create RGB classification image
rgb_image = classification.visualize(**dw_vis_params).divide(255)
probability_hillshade = rgb_image.multiply(hillshade)


def get_results():
    return {
        "s2_image": s2_image.visualize(**s2_vis_params),
        "classification": classification.visualize(**dw_vis_params),
        "probability_hillshade": probability_hillshade
    }
