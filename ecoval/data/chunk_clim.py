# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---


# %% tags=["remove-input"]


if variable == "chlorophyll":
    transformation = "log10"
else:
    transformation = None 


ds_annual = ds_model.copy()
ds_annual.tmean()
if "model" == ds_annual.variables[0]:
    ds_annual.set_longnames({"model": Variable})
else:
    ds_annual.set_longnames({variable: Variable})

ds_annual.run()

#get the min/max lon lat with actual values in ds_annual
# save as [lon_min, lon_max] and [lat_min, lat_max]
coord_ranges = (
    ds_annual
    .to_dataframe()
    .reset_index()
    .dropna()
)
lon_name = [x for x in coord_ranges.columns if "lon" in x][0]
lat_name = [x for x in coord_ranges.columns if "lat" in x][0]
coord_ranges = (
    coord_ranges
    # rename the columns to lon and lat
    .rename(columns = {lon_name: "lon", lat_name: "lat"})
    #
    .loc[:,["lon", "lat"]]
    .agg(["min", "max"])
    .to_dict()
)

lon_min = coord_ranges["lon"]["min"]
lon_max = coord_ranges["lon"]["max"]
lat_min = coord_ranges["lat"]["min"]
lat_max = coord_ranges["lat"]["max"]
if lon_max < 90:
    ds_annual.subset(lon = [lon_min, lon_max], lat = [lat_min, lat_max])
fix_grid = False
try:
    plot_model = ds_annual.pub_plot(limits = ["0%", "98%"], trans = transformation)
except:
    # this needs to be regridded
    ds_plot = ds_annual.copy()
    lons = ds_plot.to_xarray()[lon_name].values
    # flatten
    lons = list(set(lons.flatten()))
    lons.sort()
    lon_res = np.abs(lons[0] - lons[1])
    # do the same for lats
    lats = ds_plot.to_xarray()[lat_name].values
    # flatten
    lats = list(set(lats.flatten()))
    lats.sort()
    lat_res = np.abs(lats[0] - lats[1])
    # regrid
    ds_plot.to_latlon(lon = [lon_min , lon_max], lat = [lat_min, lat_max], res = [lon_res, lat_res]) 
    ds_plot.run()
    plot_model = ds_plot.pub_plot(limits = ["0%", "98%"], trans = transformation)
    fix_grid = True 

# %% tags=["remove-input"]
md(f"**Figure {i_figure}**: Annual mean {layer} {vv_name} from the model. For clarity, the colorbar is limited to the 98th percentile of the data.") 
i_figure += 1

# %% tags=["remove-input"]
ds_annual = ds_obs.copy()
ds_annual.tmean()

#get the min/max lon lat with actual values in ds_annual
# save as [lon_min, lon_max] and [lat_min, lat_max]

coord_ranges = (
    ds_annual
    .to_dataframe()
    .reset_index()
    .dropna()
)
lon_name = [x for x in coord_ranges.columns if "lon" in x][0]
lat_name = [x for x in coord_ranges.columns if "lat" in x][0]
coord_ranges = (
    coord_ranges
    # rename the columns to lon and lat
    .rename(columns = {lon_name: "lon", lat_name: "lat"})
    #
    .loc[:,["lon", "lat"]]
    .agg(["min", "max"])
    .to_dict()
)



lon_min = coord_ranges["lon"]["min"]
lon_max = coord_ranges["lon"]["max"]
lat_min = coord_ranges["lat"]["min"]
lat_max = coord_ranges["lat"]["max"]
if lon_max < 90:
    ds_annual.subset(lon = [lon_min, lon_max], lat = [lat_min, lat_max])

if not fix_grid:
    plot_obs = ds_annual.pub_plot(limits = ["0%", "98%"], trans = transformation)
else:
    ds_plot = ds_annual.copy()
    ds_plot.to_latlon(lon = [lon_min , lon_max], lat = [lat_min, lat_max], res = [lon_res, lat_res])
    plot_obs = ds_plot.pub_plot(limits = ["0%", "98%"], trans = transformation)

# %% tags=["remove-input"]
md(f"**Figure {i_figure}**: Annual {layer} mean {vv_name} from the observations. For clarity, the colorbar is limited to the 98th percentile of the data.")
i_figure += 1

# %% tags=["remove-cell"]
# Plot them on the same scale
ds_both = ds_model.copy()
ds_both.rename({ds_both.variables[0]: "model"})
ds_both.append(ds_obs)
ds_both.rename({ds_obs.variables[0]: "observation"})
ds_both.merge(match = "month")
ds_both.run()
ds_both.variables

#get the min/max lon lat with actual values in ds_annual
# save as [lon_min, lon_max] and [lat_min, lat_max]
coord_ranges = (
    ds_both
    .to_dataframe()
    .reset_index()
    .dropna()
)
lon_name = [x for x in coord_ranges.columns if "lon" in x][0]
lat_name = [x for x in coord_ranges.columns if "lat" in x][0]
coord_ranges = (
    coord_ranges
    # rename the columns to lon and lat
    .rename(columns = {lon_name: "lon", lat_name: "lat"})
    #
    .loc[:,["lon", "lat"]]
    .agg(["min", "max"])
    .to_dict()
)

lat_min = coord_ranges["lat"]["min"]
lat_max = coord_ranges["lat"]["max"]
if lon_max < 90:
    ds_both.subset(lon = [lon_min, lon_max], lat = [lat_min, lat_max])

if fix_grid:
    ds_both.to_latlon(lon = [lon_min , lon_max], lat = [lat_min, lat_max], res = [lon_res, lat_res])


# %% tags=["remove-cell"]
import matplotlib.pyplot as plt

plt.subplots_adjust(wspace=20, hspace=20)

fig = plt.figure(figsize=(10, 10))

# Create 4x4 Grid

gs = fig.add_gridspec(nrows=1, ncols=2, wspace = 0.35, hspace = 0)

# get limits..

z_min = (
    ds_both
    .to_dataframe()
    .reset_index()
    .dropna()
    .loc[:,["model", "observation"]]
    # get the 2nd percentils
    # .groupby("variable")
    .quantile(0.02)
    .min()
)

# get the 98th percentils

z_max = (
    ds_both
    .to_dataframe()
    .reset_index()
    .dropna()
    .loc[:,["model", "observation"]]
    .quantile(0.98)
    .max()
)
ds_both.tmean()
# fix the units

ds_both.set_units({"observation": ds_both.contents.query("variable == 'model'").reset_index().unit.values[0]})
# chang longname
try:
    ds_both.set_longnames({"observation": ds_both.contents.query("variable == 'model'").reset_index().long_name.values[0]}) 
except:
    ds_both.set_longnames({"observation": ds_both.contents.query("variable == 'observation'").reset_index().long_name.values[0]})  
ds_both.pub_plot(variable  = "model", limits = [z_min, z_max], title = "Model", fig = fig, gs = gs[0,0], trans = transformation)


ds_both.pub_plot(variable  = "observation", limits = [z_min, z_max], title = "Observation", fig = fig, gs = gs[0,1], trans = transformation)

# %% tags=["remove-input"]
fig




# %% tags=["remove-input"]
md(f"**Figure {i_figure}**: Annual mean {layer} {vv_name} from the model and observations.")
i_figure += 1
