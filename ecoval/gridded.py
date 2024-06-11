import os
import glob
import warnings
import time
import numpy as np
import nctoolkit as nc

from ecoval.fixers import tidy_warnings
from ecoval.utils import extension_of_directory, get_extent
from ecoval.session import session_info


def write_report(x):
    # append x to report
    with open("matchup_report.md", "a") as f:
        f.write(x + "\n")
        # add blank line
        f.write("\n")


def gridded_matchup(
    df_mapping=None,
    folder=None,
    var_choice=None,
    exclude=None,
    surface=None,
    start=None,
    sim_start=None,
    sim_end=None,
    domain = "nws",
    strict=True,
    lon_lim=None,
    lat_lim=None,
    times_dict=None,
    ds_thickness = None
):
    """
    Function to create gridded matchups for a given set of variables

    Parameters
    ----------
    df_mapping : pandas.DataFrame
        DataFrame containing the mapping between model variables and gridded observations
    folder : str
        Path to folder containing model data
    var_choice : list
        List of variables to create matchups for
    exclude : list
        List of strings to exclude from the file search
    surface : str
        Surface to use for matchups. Either "top" or "bottom"
    start : int
        Start year for matchups
    sim_start : int
        Start year for model simulations
    sim_end : int
        End year for model simulations
    domain : str
        Domain to use for matchups. Either "NWS" or "global"
        This indicates whether the matchups use northwest European shelf data or global data
    ds_thickness : str or nctoolkit DataSet
        File path to thickness file

    """
    data_dir = session_info["data_dir"]

    all_df = df_mapping
    # if model_variable is None remove from all_df
    good_model_vars = [x for x in all_df.model_variable if x is not None]

    all_df = all_df.query("model_variable in @good_model_vars").reset_index(drop=True)

    all_df = all_df.dropna()

    vars = [
        "ammonium",
        "chlorophyll",
        "nitrate",
        "phosphate",
        "oxygen",
        "silicate",
        "salinity",
        "poc",
        "temperature",
        "co2flux",
        "pco2",
        "ph",
        "alkalinity",
        "doc",
    ]
    vars = [x for x in vars if x in var_choice]
    vars.sort() 

    if len(vars) > 0:
        # first up, do the top

        mapping = dict()

        for vv in vars:
            out = glob.glob(f"matched/gridded/{domain}/{vv}/*_{vv}_surface.nc")
            if len(out) > 0:
                if session_info["overwrite"] is False:
                    continue
            # figure out the data source
            #
            dir_var = f"{data_dir}/gridded/user/{vv}"
            # check if this directory is empty
            if len(glob.glob(dir_var + "/*")) == 0:
                dir_var = f"{data_dir}/gridded/{domain}/{vv}"
            if len(glob.glob(dir_var + "/*")) == 0:
                dir_var = f"{data_dir}/gridded/global/{vv}"

            vv_source = [
                os.path.basename(x).replace(".txt", "")
                for x in glob.glob(dir_var + "/*")
                if ".txt" in x
            ][0]
            # out_dir = f"matched/gridded/{vv_source}"

            # if not os.path.exists(out_dir):
            #     os.makedirs(out_dir)

            print("**********************")
            #
            vv_name = vv
            if vv == "poc":
                vv_name = "particulate organic carbon"
            if vv == "doc":
                vv_name = "dissolved organic carbon"
            if vv == "co2flux":
                vv_name = "sea-air CO2 flux"
            if vv == "ph":
                vv_name = "pH"

            print(
                f"Matching up surface {vv_name} with {vv_source.upper()} gridded data"
            )
            print("**********************")
            df = df_mapping.query("variable == @vv").reset_index(drop=True)
            if len(df) > 0:
                mapping[vv] = list(df.query("variable == @vv").model_variable)[0]

                selection = []
                try:
                    selection += mapping[vv].split("+")
                except:
                    selection = selection

                patterns = set(df.pattern)
                if len(patterns) > 1:
                    raise ValueError(
                        "Something strange going on in the string patterns. Unable to handle this. Bug fix time!"
                    )
                pattern = list(patterns)[0]

                final_extension = extension_of_directory(folder)
                paths = glob.glob(folder + final_extension + pattern)

                for exc in exclude:
                    paths = [x for x in paths if f"{exc}" not in os.path.basename(x)]

                new_paths = []
                # set up model_grid if it doesn't exist

                # This really should be a function....
                if not os.path.exists("matched/model_grid.csv"):
                    ds_grid = nc.open_data(paths[0], checks=False)
                    var = ds_grid.variables[0]
                    ds_grid.subset(variables=var, time = 0)
                    if surface == "top":
                        ds_grid.top()
                    else:
                        ds_grid.bottom()
                    ds_grid.as_missing(0)
                    if max(ds_grid.contents.npoints) == 111375:
                        amm7_out = "matched/amm7.txt"
                        # create empty file
                        with open(amm7_out, "w") as f:
                            f.write("")

                        ff_grid = f"{data_dir}/amm7_val_subdomains.nc"
                        ds_grid.cdo_command(f"setgrid,{ff_grid}")
                    df_grid = ds_grid.to_dataframe().reset_index().dropna()
                    columns = [x for x in df_grid.columns if "lon" in x or "lat" in x]
                    df_grid = df_grid.loc[:, columns].drop_duplicates()
                    if not os.path.exists("matched"):
                        os.makedirs("matched")
                    df_grid.to_csv("matched/model_grid.csv", index=False)

                all_years = []
                for ff in paths:
                    all_years += list(times_dict[ff].year)
                all_years = list(set(all_years))

                sim_years = range(sim_start, sim_end + 1)
                if start is not None:
                    years = [x for x in all_years if x in sim_years]
                else:
                    years = all_years
                # now simplify paths, so that only the relevant years are used
                new_paths = []

                for ff in paths:
                    if len([x for x in times_dict[ff].year if x in years]) > 0:
                        new_paths.append(ff)

                paths = list(set(new_paths))
                paths.sort()

                # get the number of paths

                n_paths = len(paths)

                # Write to report
                write_report(f"### Matchups for {vv}")
                write_report(f"Number of paths: {n_paths}")
                # minimum year
                write_report(f"Minimum year: {min(years)}")
                # maximum year
                write_report(f"Maximum year: {max(years)}")
                # write the list of files
                write_report(f"Files used for {vv}:")
                write_report("```")
                paths.sort()
                for ff in paths:
                    write_report(ff)
                write_report("```")

                # add a pagebreak
                write_report("\\newpage")

                # figure out if cdo or nco is faster....

                use_nco = False

                with warnings.catch_warnings(record=True) as w:

                    if vv_source == "glodap":
                        for ff in paths:
                            ff_years = times_dict[ff].year
                            if (
                                len([x for x in ff_years if x in range(1971, 2015)])
                                == 0
                            ):
                                paths.remove(ff)


                    if vv_source == "woa":
                        ds_vertical = nc.open_data(paths, checks=False)
                    else:
                        ds_surface = nc.open_data(paths, checks=False)

                    if vv_source == "woa":
                        # handle this differently
                        ds_vertical = nc.open_data()
                        for mm in range(1,13):
                            mm_paths = []
                            for ff in paths:
                                if mm in times_dict[ff].month.values:
                                    mm_paths.append(ff)
                            mm_paths = list(set(mm_paths))

                            # nco_command = f'ncra -y mean -v {",".join(selection)}' 
                            ds_mm = nc.open_data(mm_paths, checks=False)
                            # ds_mm.nco_command(nco_command, ensemble = False)
                            ds_mm.subset(variables=selection)
                            ds_mm.subset(month = mm, time = 0)
                            ds_mm.tmean(["year", "month"])
                            ds_mm.ensemble_mean()
                            ds_mm.as_missing(0)
                            ds_mm.run()
                            ds_vertical.append(ds_mm)

                        ds_surface = ds_vertical.copy()
                        ds_vertical.ensemble_mean(nco = True)
                    else:
                        if use_nco:
                            if vv_source != "woa":
                                ds_surface.nco_command(f"ncks -F -d deptht,1 -v {nco_selection}")
                                ds_surface.as_missing(0)
                                ds_surface.tmean(["year", "month"])
                            else:
                                ds_surface.nco_command(f"ncks -F -v {nco_selection}")
                                ds_surface.as_missing(0)
                                ds_surface.tmean(["year", "month"])
                                ds_surface = ds_vertical.copy()
                        else:
                            if vv_source != "woa":
                                ds_surface.subset(variables=selection)
                                if surface == "top":
                                    ds_surface.top()
                                else:
                                    ds_surface.bottom()
                                ds_surface.as_missing(0)
                                ds_surface.tmean(["year", "month"])

                    if vv_source == "glodap":
                        ds_surface.merge("time")
                        ds_surface.tmean()

                    # the code below needs to be simplifed
                    # essentially anything with a + in the mapping should be split out
                    # and then the command should be run for each variable

                    var_unit = None
                    ignore_later = []
                    if vv_source != "woa":
                        for vv in list(df.variable):
                            if "+" in mapping[vv]:
                                command = f"-aexpr,{vv}=" + mapping[vv]
                                ds_surface.cdo_command(command)
                                drop_these = mapping[vv].split("+")
                                ds_contents = ds_surface.contents
                                ds_contents = ds_contents.query("variable in @drop_these")
                                var_unit = ds_contents.unit[0]
                                ds_surface.drop(variables=drop_these)
                                ignore_later.append(vv)

                                ds_surface.run()
                                for key in mapping:
                                    if key not in ignore_later:
                                        if mapping[key] in ds_vertical.variables:
                                            ds_surface.rename({mapping[key]: key})
                                if "chlorophyll" in list(df.variable):
                                    if var_unit is not None:
                                        ds_surface.set_units({"chlorophyll": var_unit})
                                        ds_surface.set_longnames(
                                            {"chlorophyll": "Total chlorophyll concentration"}
                                        )
                                if "poc" in list(df.variable):
                                    ds_surface.set_units({"poc": var_unit})
                                    ds_surface.set_longnames(
                                        {"poc": "Particulate organic carbon concentration"}
                                    )
                                if "doc" in list(df.variable):
                                    ds_surface.set_units({"doc": var_unit})
                                    ds_surface.set_longnames(
                                        {"doc": "Dissolved organic carbon concentration"}
                                    )

                                ds_surface.run()
                                ds_surface.tmean(["year", "month"])
                                ds_surface.merge("time")
                                ds_surface.subset(years=years)
                                ds_surface.run()

                tidy_warnings(w)

                if surface == "top":
                    ds_surface.top()
                    ds_surface.run()
                else:
                    ds_surface.bottom()

                # figure out the start and end year
                start_year = min(ds_surface.years)
                end_year = max(ds_surface.years)
                if vv_source == "woa":
                    # ds_surface = ds.copy()
                    ds_vertical.ensemble_mean(nco = True)

                # Read in the monthly observational data
                vv_file = nc.create_ensemble(dir_var)
                vv_file = [x for x in vv_file if "annual" not in x]
                # except:
                # vv_file = nc.create_ensemble(dir_var)
                ds_obs = nc.open_data(
                    vv_file,
                    checks=False,
                )
                if vv_source == "occci":
                    ds_obs.subset(variable="chlor_a")
                    ds_obs.subset(years = range(start_year, end_year + 1))

                # read in the annual observational data for WOA
                if vv_source == "woa":
                    vv_file = nc.create_ensemble(dir_var)
                    vv_file = [x for x in vv_file if "annual" in x]
                    ds_obs_annual = nc.open_data(
                        vv_file,
                        checks=False,
                    )
                    ds_obs_annual.rename({ds_obs_annual.variables[0]: "observation"})
                    if len(ds_obs_annual.variables) > 1:
                        raise ValueError(f"Please ensure only one variable in {vv}!")

                obs_years = ds_obs.years

                if vv_source != "woa":
                    if len(obs_years) == 1:
                        ds_surface.tmean("month")
                    else:
                        ds_surface.tmean(["year", "month"])

                amm7 = False
                if domain == "nws":
                    if max(ds_surface.contents.npoints) == 111375:
                        ds_surface.fix_amm7_grid()
                        amm7 = True
                        ds_surface.subset(lon=[-19, 9], lat=[41, 64.3])

                if vv in ["poc", "doc"]:
                    if strict:
                        ds_obs.subset(years=years)
                    ds_obs.merge("time")
                    ds_obs.tmean("month")
                    ds_surface.tmean("month")

                if vv in ["temperature"]:
                    if strict:
                        ds_obs.subset(years=years)
                    ds_obs.subset(years=years)
                    ds_obs.tmean(["year", "month"])
                    ds_obs.merge("time")
                    ds_obs.tmean(["year", "month"])
                
                if vv in ["salinity"] and domain != "nws":
                    if vv_source != "woa":
                        ds_obs.top()
                    sub_years = [x for x in ds_vertical.years if x in ds_obs.years]
                    ds_obs.subset(years=sub_years)
                    ds_surface.subset(years = sub_years)
                    ds_obs.merge("time")
                    ds_obs.tmean("month")
                    ds_surface.merge("time")
                    ds_surface.tmean("month")
                    ds_obs_annual.subset(years = sub_years)
                    ds_obs_annual.tmean()
                if vv in ["chlorophyll"] and domain != "nws":
                    ds_obs.top()
                    sub_years = [x for x in ds_surface.years if x in ds_obs.years]
                    ds_obs.subset(years=sub_years)
                    ds_surface.subset(years = sub_years)
                    ds_obs.merge("time")
                    ds_obs.tmean("month")
                    ds_surface.merge("time")
                    ds_surface.tmean("month")


                if vv not in ["poc", "temperature"]:
                    if len(ds_obs.times) > 12:
                        ds_obs.subset(years=years)

                if vv_source == "occci":
                    ds_obs.subset(variable="chlor_a")

                ds_xr = ds_surface.to_xarray()
                lon_name = [x for x in ds_xr.coords if "lon" in x]
                lat_name = [x for x in ds_xr.coords if "lat" in x]
                lon = ds_xr[lon_name[0]].values
                lat = ds_xr[lat_name[0]].values
                lon_max = lon.max()
                lon_min = lon.min()
                lat_max = lat.max()
                lat_min = lat.min()

                # figure out the lon/lat extent in the model
                lons = [lon_min, lon_max]
                lats = [lat_min, lat_max]
                # start of with the raw coords
                # This will not work with nemo, which outputs the grid incorrectly
                # so we will check if the step between the first lon/lat and the second lon/lat is
                # far bigger than the rest. If this is the case, the first should be ignored
                # get the lon/lat values
                lon_vals = ds_xr[lon_name[0]].values
                lat_vals = ds_xr[lat_name[0]].values
                # make them unique and ordered, and 1d
                lon_vals = np.unique(lon_vals)
                # make a list
                lon_vals = lon_vals.tolist()
                diff_1 = lon_vals[1] - lon_vals[0]
                diff_2 = lon_vals[2] - lon_vals[1]
                diff_3 = lon_vals[3] - lon_vals[2]
                if diff_1 / diff_2 > 10:
                    if diff_1 / diff_3 > 10:
                        lons[0] = lon_vals[1]
                # do it for lats
                lat_vals = np.unique(lat_vals)
                lat_vals = lat_vals.tolist()
                diff_1 = lat_vals[1] - lat_vals[0]
                diff_2 = lat_vals[2] - lat_vals[1]
                diff_3 = lat_vals[2] - lat_vals[1]
                if diff_1 / diff_2 > 10:
                    if diff_1 / diff_3 > 10:
                        lats[0] = lat_vals[1]

                lon_min_model = lons[0]
                lon_max_model = lons[1]
                lat_min_model = lats[0]
                lat_max_model = lats[1]

                # now do the same for the obs
                ds_xr = ds_obs.to_xarray()
                lon_name = [x for x in ds_xr.coords if "lon" in x]
                lat_name = [x for x in ds_xr.coords if "lat" in x]
                lon = ds_xr[lon_name[0]].values
                lat = ds_xr[lat_name[0]].values
                lon_max = lon.max()
                lon_min = lon.min()
                lat_max = lat.max()
                lat_min = lat.min()

                lon_min = max(lon_min, lon_min_model)
                lon_max = min(lon_max, lon_max_model)
                lat_min = max(lat_min, lat_min_model)
                lat_max = min(lat_max, lat_max_model)

                lons = [lon_min, lon_max]
                lats = [lat_min, lat_max]

                if domain != "global":
                    ds_surface.subset(lon=lons, lat=lats)
                    ds_obs.subset(lon=lons, lat=lats)

                if domain == "global":
                    model_extent = get_extent(ds_surface[0])
                    obs_extent = get_extent(ds_obs[0])
                    lon_min = max(model_extent[0], obs_extent[0])
                    lon_max = min(model_extent[1], obs_extent[1])
                    lat_min = max(model_extent[2], obs_extent[2])
                    lat_max = min(model_extent[3], obs_extent[3])
                    # make sure lon_min is greater than -180
                    if lon_min < -180:
                        lon_min = -180
                    if lon_max > 180:
                        lon_max = 180
                    if lat_min < -90:
                        lat_min = -90
                    if lat_max > 90:
                        lat_max = 90

                    lons = [lon_min, lon_max]
                    lats = [lat_min, lat_max]
                    ds_surface.subset(lon=lons, lat=lats)
                    ds_obs.subset(lon=lons, lat=lats)

                n1 = ds_obs.contents.npoints[0]
                n2 = ds_surface.contents.npoints[0]

                if n1 >= n2:
                    ds_obs.regrid(ds_surface, method="nn")
                else:
                    ds_surface.regrid(ds_obs, method="nn")

                ds_obs.rename({ds_obs.variables[0]: "observation"})
                ds_surface.merge("time")
                ds_surface.rename({ds_surface.variables[0]: "model"})

                # it is possible the years do not overlap, e.g. with satellite Chl
                if len(ds_surface.times) > 12:
                    years1 = ds_surface.years
                    years2 = ds_obs.years
                    all_years = [x for x in years1 if x in years2]
                    if len(all_years) != len(years1):
                        if len(all_years) != len(years2):
                            ds_obs.subset(years=all_years)
                            ds_surface.subset(years=all_years)
                            ds_obs.run()
                            ds_surface.run()
                if len(ds_obs) > 1:
                    ds_obs.merge("time")

                ds_obs.run()
                ds_surface.run()

                if vv == "doc":
                    ds_obs * 12.011
                    ds_surface + (40 * 12.011)

                if vv_source != "woa":
                    ds_obs.top()

                if vv_source == "woa":
                    levels = ds_obs_annual.levels
                    levels = [x for x in levels if x >= np.min(ds_vertical.levels)]
                    ds1 = ds_vertical.copy()
                    ds1.merge("time")
                    ds1.tmean()
                    ds1.rename({ds1.variables[0]: "model"})
                    if ds_thickness is not None:
                        ds1.vertical_interp(levels, thickness = ds_thickness) 
                    else:
                        ds1.vertical_interp(levels, fixed = True)
                    if n1 >= n2:
                        ds_obs_annual.regrid(ds1, method="nn")
                    else:
                        ds1.regrid(ds_obs_annual, method="nn")
                    ds_obs_annual.vertical_interp(levels, fixed = True)
                    ds_obs_annual.append(ds1)
                    ds_obs_annual.merge("variable")

                if surface == "top":
                    ds_surface.top()
                else:
                    ds_surface.bottom()
                ds_obs.top()

                if vv_source == "occci":
                    years = [x for x in ds_obs.years if x in ds_surface.years]
                    years = list(set(years))

                    ds_obs.subset(years=years)
                    ds_obs.tmean(["year", "month"])
                    ds_obs.merge("time")
                    ds_obs.tmean(["year", "month"])
                    ds_surface.subset(years=years)
                    ds_surface.tmean(["year", "month"])

                ds_obs.append(ds_surface)

                if len(ds_surface.times) > 12:
                    ds_obs.merge("variable", match=["year", "month"])
                else:
                    ds_obs.merge("variable", match="month")
                ds_obs.nco_command(f"ncatted -O -a start_year,global,o,c,{start_year}")
                ds_obs.nco_command(f"ncatted -O -a end_year,global,o,c,{end_year}")
                ds_obs.set_fill(-9999)
                ds_mask = ds_obs.copy()
                ds_mask.assign( mask_these=lambda x: -1e30 * ((isnan(x.observation) + isnan(x.model)) > 0), drop=True,)
                ds_mask.as_missing([-1e40, -1e20])
                ds_obs + ds_mask

                # fix the co2 flux units
                if vv == "co2flux":
                    ds_obs.assign(model=lambda x: x.model * -0.365)
                    ds_obs.set_units({"model": "mol/m2/yr"})
                    ds_obs.set_units({"observation": "mol/m2/yr"})

                # figure out if the temperature is in degrees C
                if vv == "temperature":
                    if ds_obs.to_xarray().model.max() > 100:
                        ds_obs.assign(model=lambda x: x.model - 273.15)
                    if ds_obs.to_xarray().observation.max() > 100:
                        ds_obs.assign(observation=lambda x: x.observation - 273.15)
                    # set the units
                    ds_obs.set_units({"model": "degrees C"})
                    ds_obs.set_units({"observation": "degrees C"})
                # # now, we need to exclude data outside the lon/lat range with data

                out_file = f"matched/gridded/{domain}/{vv}/{vv_source}_{vv}_surface.nc"
                # check directory exists for out_file
                if not os.path.exists(os.path.dirname(out_file)):
                    os.makedirs(os.path.dirname(out_file))
                # remove the file if it exists
                if os.path.exists(out_file):
                    os.remove(out_file)
                ds_obs.set_precision("F32")
                if vv == "salinity" and domain != "nws":
                    ds_obs.tmean("month")
                ds_surface = ds_obs.copy()
                if vv_source == "woa":
                    ds_surface.top()
                if lon_lim is not None and lat_lim is not None:
                    ds_surface.subset(lon=lon_lim, lat=lat_lim)
                ds_surface.to_nc(out_file, zip=True, overwrite=True)

                # now do the masking etc.

                if vv_source == "woa": 
                    out_file = f"matched/gridded/{domain}/{vv}/{vv_source}_{vv}_vertical.nc"
                    ds_obs_annual.set_precision("F32")

                    ds_obs_annual.set_fill(-9999)
                    ds_mask = ds_obs_annual.copy()
                    ds_mask.assign( mask_these=lambda x: -1e30 * ((isnan(x.observation) + isnan(x.model)) > 0), drop=True,)
                    ds_mask.as_missing([-1e40, -1e20])
                    ds_mask.run()
                    ds_obs_annual + ds_mask
                    if os.path.exists(out_file):
                        os.remove(out_file)
                    if not os.path.exists(os.path.dirname(out_file)):
                        os.makedirs(os.path.dirname(out_file))

                    lons = [lon_min, lon_max]
                    lats = [lat_min, lat_max]
                    ds_obs_annual.subset(lon=lons, lat=lats)
                    if lon_lim is not None and lat_lim is not None:
                        ds_obs_annual.subset(lon=lon_lim, lat=lat_lim)

                    ds_obs_annual.to_nc(out_file, zip=True, overwrite=True)


        return None
