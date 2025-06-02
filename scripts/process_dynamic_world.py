

# import ee
# import geopandas as gpd
# from shapely.geometry import mapping

# # Initialize the Earth Engine API
# ee.Initialize(project="ee-officialsatbir23")

# # Load your AOI shapefile
# gdf = gpd.read_file("E:\D-Drive\GEE-project\data\BV_Rhone.shp")
# geometry = gdf.geometry.unary_union.__geo_interface__
# roi = ee.Geometry(geometry)

# # Define time range
# start_date = '2020-01-01'
# end_date = '2021-01-01'

# # Sentinel-2 Image Collection: Filter and clip to region
# s2 = (
#     ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
#     .filterDate(start_date, end_date)
#     .filterBounds(roi)
#     .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 35))
#     .map(lambda img: img.clip(roi))
# )

# # Create median composite
# s2_image = s2.mode()
# s2_vis_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 5000}

# # Load Dynamic World Image Collection: Filter and clip
# dw = (
#     ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
#     .filterDate(start_date, end_date)
#     .filterBounds(roi)
#     .map(lambda img: img.clip(roi))
# )

# # Get mode classification (most frequent land class)
# classification = dw.select("label").mode()

# # Probability bands to calculate hillshade
# probability_bands = [
#     "water", "trees", "grass", "flooded_vegetation", "crops",
#     "shrub_and_scrub", "built", "bare", "snow_and_ice"
# ]

# # Get mean probability image
# prob_image = dw.select(probability_bands).mean()

# # Compute top class confidence and hillshade
# top1_probability = prob_image.reduce(ee.Reducer.max())
# top1_confidence = top1_probability.multiply(100).int()
# hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)

# # Color palette for land cover
# dw_vis_params = {
#     "min": 0,
#     "max": 8,
#     "palette": [
#         "#419BDF",  # Water
#         "#397D49",  # Trees
#         "#88B053",  # Grass
#         "#7A87C6",  # Flooded vegetation
#         "#E49635",  # Crops
#         "#DFC35A",  # Shrub and scrub
#         "#C4281B",  # Built
#         "#A59B8F",  # Bare
#         "#B39FE1"   # Snow and ice
#     ]
# }

# # Create RGB classification image
# rgb_image = classification.visualize(**dw_vis_params).divide(255)
# probability_hillshade = rgb_image.multiply(hillshade)


# def get_results():
#     return {
#         "s2_image": s2_image.visualize(**s2_vis_params),
#         "classification": classification.visualize(**dw_vis_params),
#         "probability_hillshade": probability_hillshade
#     }


import ee
import geopandas as gpd
from shapely.geometry import mapping

# Initialize Earth Engine
ee.Initialize(project="ee-officialsatbir23")

# Load AOI from shapefile
gdf = gpd.read_file("E:/D-Drive/GEE-project/data/BV_Rhone.shp")
geometry = gdf.geometry.unary_union.__geo_interface__
roi = ee.Geometry(geometry)

# Time range
start_date = '2020-01-01'
end_date = '2021-01-01'

# Sentinel-2 Collection: Use fewer bands and median composite
s2_bands = ["B4", "B3", "B2"]
s2 = (
    ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filterDate(start_date, end_date)
    .filterBounds(roi)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 35))
    .select(s2_bands)
)

# Composite using median (lighter than .mode)
s2_median = s2.median().clip(roi)
s2_vis_params = {"bands": s2_bands, "min": 0, "max": 5000}

# Dynamic World classification mode (we aggregate monthly to avoid overload)
def monthly_mode(year, month):
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, 'month')
    month_ic = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterDate(start, end)
        .filterBounds(roi)
        .select("label")
    )
    return month_ic.mode().set("month", month)

# Compute monthly modes and make one final mode image
months = ee.List.sequence(1, 12)
monthly_modes = months.map(lambda m: monthly_mode(2020, ee.Number(m)))
dw_mode_ic = ee.ImageCollection(monthly_modes)
dw_mode = dw_mode_ic.mode().clip(roi)

# Color parameters
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

# Probability Image Mean — compute over monthly mean
def monthly_prob_mean(year, month):
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, 'month')
    prob_bands = [
        "water", "trees", "grass", "flooded_vegetation", "crops",
        "shrub_and_scrub", "built", "bare", "snow_and_ice"
    ]
    return (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterDate(start, end)
        .filterBounds(roi)
        .select(prob_bands)
        .mean()
        .set("month", month)
    )

monthly_probs = months.map(lambda m: monthly_prob_mean(2020, ee.Number(m)))
prob_image = ee.ImageCollection(monthly_probs).mean().clip(roi)

# Top class confidence and hillshade
top1_probability = prob_image.reduce(ee.Reducer.max())
top1_confidence = top1_probability.multiply(100).int()
hillshade = ee.Terrain.hillshade(top1_confidence).divide(255)

# Create RGB image and combine with hillshade
rgb_image = dw_mode.visualize(**dw_vis_params).divide(255)
probability_hillshade = rgb_image.multiply(hillshade)

# Results
def get_results():
    return {
        "s2_image": s2_median.visualize(**s2_vis_params),
        "classification": dw_mode.visualize(**dw_vis_params),
        "probability_hillshade": probability_hillshade
    }
