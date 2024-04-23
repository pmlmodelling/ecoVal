from ecoval.utils import get_datadir
import pkg_resources
import pandas as pd
import glob
import nctoolkit as nc
from ecoval.matchall import matchup
from ecoval.fixers import tidy_name
from ecoval.regionals import global_regionals
import webbrowser
from ecoval.chunkers import add_chunks
import os


def fix_toc(book_dir):
    paths = glob.glob(f"{book_dir}/notebooks/*.ipynb")
    variables = list(pd.read_csv("matched/mapping.csv").variable)
    variables.sort()

    vv_dict = dict()
    for vv in variables:
        if vv != "ph":
            vv_paths = [os.path.basename(x) for x in paths if vv in x]
            if len(vv_paths) > 0:
                vv_dict[vv] = vv_paths
        else:
            vv_paths = [
                os.path.basename(x)
                for x in paths
                if vv in x and "phos" not in x and "chlo" not in x and "occci" not in x
            ]
            if len(vv_paths) > 0:
                vv_dict[vv] = vv_paths
    # get summary docs
    ss_paths = [os.path.basename(x) for x in paths if "summary" in x]

    out = f"{book_dir}/_toc.yml"

    # write line by line to out
    with open(out, "w") as f:
        # "format: jb-book"
        x = f.write("format: jb-book\n")
        x = f.write("root: intro\n")
        x = f.write("parts:\n")
        x = f.write(f"- caption: Introduction\n")
        x = f.write("  chapters:\n")
        x = f.write(f"  - file: notebooks/000_info.ipynb\n")

        # loop over variables in each vv_dict
        # value is the file in the chapter section
        # key is the variable name, so is the section
        for vv in vv_dict.keys():
            # capitalize if not ph
            if vv != "ph":
                vv_out = vv.capitalize()
            if vv.lower() in ["poc", "doc"]:
                vv_out = vv.upper() 
            # correct ph
            if vv == "ph":
                vv_out = "pH"
            x = f.write(f"- caption: {vv_out}\n")
            x = f.write("  chapters:\n")
            for file in vv_dict[vv]:
                x = f.write(f"  - file: notebooks/{file}\n")

        x = f.write(f"- caption: Summaries\n")
        x = f.write("  chapters:\n")
        for file in ss_paths:
            x = f.write(f"  - file: notebooks/{file}\n")


def fix_toc_comparison(book_dir):

    out = f"{book_dir}/compare/_toc.yml"
    # write line by line to out
    with open(out, "w") as f:
        # "format: jb-book"
        x = f.write("format: jb-book\n")
        x = f.write("root: intro\n")
        x = f.write("parts:\n")
        x = f.write(f"- caption: Comparisons with gridded surface observations\n")
        x = f.write("  chapters:\n")
        x = f.write(f"  - file: notebooks/comparison_bias.ipynb\n")
        x = f.write(f"  - file: notebooks/comparison_spatial.ipynb\n")
        x = f.write(f"  - file: notebooks/comparison_seasonal.ipynb\n")


def compare(model_dict=None):
    """
    This function will compare the validition output from multiple models.
    """

    # make a folder called book/compare

    data_path = pkg_resources.resource_filename(__name__, "data/mask.py")
    if not os.path.exists(f"book/compare/notebooks/mask.py"):
        if not os.path.exists("book/compare/notebooks"):
            # create directory recursively
            os.makedirs("book/compare/notebooks")
        shutil.copyfile(data_path, "book/compare/notebooks/mask.py")

    if not os.path.exists("book/compare"):
        # create directory recursively
        os.makedirs("book/compare")

    # move toc etc to book/compare

    data_path = pkg_resources.resource_filename(__name__, "data/_toc.yml")

    out = "book/compare/" + os.path.basename(data_path)

    shutil.copyfile(data_path, out)

    fix_toc_comparison()

    data_path = pkg_resources.resource_filename(__name__, "data/requirements.txt")

    out = "book/compare/" + os.path.basename(data_path)

    shutil.copyfile(data_path, out)

    data_path = pkg_resources.resource_filename(__name__, "data/intro.md")

    out = "book/compare/" + os.path.basename(data_path)

    shutil.copyfile(data_path, out)

    # copy config

    data_path = pkg_resources.resource_filename(__name__, "data/_config.yml")

    out = "book/compare/" + os.path.basename(data_path)

    shutil.copyfile(data_path, out)

    # copy the comparison_seasonal notebook

    # make sure the directory exists

    if not os.path.exists("book/compare/notebooks"):
        # create directory recursively
        os.makedirs("book/compare/notebooks")

    file1 = pkg_resources.resource_filename(__name__, "data/comparison_seasonal.ipynb")
    if len(glob.glob("book/compare/notebooks/*comparison_seasonal.ipynb")) == 0:
        shutil.copyfile(file1, "book/compare/notebooks/comparison_seasonal.ipynb")

    model_dict_str = str(model_dict)

    with open("book/compare/notebooks/comparison_seasonal.ipynb", "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace("model_dict_str", model_dict_str)

    # Write the file out again

    with open("book/compare/notebooks/comparison_seasonal.ipynb", "w") as file:
        file.write(filedata)

    # now sort out the comparison_spatial notebook

    file1 = pkg_resources.resource_filename(__name__, "data/comparison_spatial.ipynb")
    if len(glob.glob("book/compare/notebooks/*comparison_spatial.ipynb")) == 0:
        shutil.copyfile(file1, "book/compare/notebooks/comparison_spatial.ipynb")

    model_dict_str = str(model_dict)

    with open("book/compare/notebooks/comparison_spatial.ipynb", "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace("model_dict_str", model_dict_str)

    # Write the file out again

    with open("book/compare/notebooks/comparison_spatial.ipynb", "w") as file:
        file.write(filedata)

    # now to comparison_bias

    file1 = pkg_resources.resource_filename(__name__, "data/comparison_bias.ipynb")

    if len(glob.glob("book/compare/notebooks/*comparison_bias.ipynb")) == 0:
        shutil.copyfile(file1, "book/compare/notebooks/comparison_bias.ipynb")

    model_dict_str = str(model_dict)

    with open("book/compare/notebooks/comparison_bias.ipynb", "r") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace("model_dict_str", model_dict_str)

    # Write the file out again

    with open("book/compare/notebooks/comparison_bias.ipynb", "w") as file:
        file.write(filedata)

    # add the chunks

    # sync the notebooks

    os.system("jupytext --set-formats ipynb,py:percent book/compare/notebooks/*.ipynb")

    add_chunks()

    # fix the chunks
    os.system("jupytext --sync book/compare/notebooks/*.ipynb")

    # loop through notebooks and change fast_plot_value to fast_plot

    for ff in glob.glob("book/compare/notebooks/*.ipynb"):
        with open(ff, "r") as file:
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("fast_plot_value", "False")

        # Write the file out again
        with open(ff, "w") as file:
            file.write(filedata)

    os.system("jupyter-book build book/compare/")
    import webbrowser

    webbrowser.open("file://" + os.path.abspath("book/compare/_build/html/index.html"))


def validate(title="Automated model evaluation", author=None):
    # docstring
    """
    This function will run the model evaluation for all of the available datasets.

    Parameters
    ----------
    title : str
        The title of the book. Default is "Automated model evaluation"
    author : str
        The author of the book. Default is None

    Returns
    -------
    None
    """
    import os
    data_dir = get_datadir()
    path_df = []

    fast_plot = False

    # figure out of "book/notebooks" has ipynb files

    empty = True

    # book directory is book, book1, book2, book10 etc.

    # create a new name if one already exists
    i = 0
    book_dir = "book"

    if os.path.exists("book"):
        #get user input to decide if it should be removed
        user_input = input("book directory already exists. This will be emptied and replaced. Do you want to proceed? (y/n): ")
        if user_input.lower() == "y":
            while True:
                files = glob.glob("book/**/**/**", recursive=True)
                # list all files in book, recursively
                for ff in files:
                    if ff.startswith("book"):
                        try:
                            os.remove(ff)
                        except:
                            pass
                files = glob.glob("book/**/**/**", recursive=True)
                # only list files
                files = [x for x in files if os.path.isfile(x)]
                if len(files) == 0:
                    break
        else:
            print("Exiting")
            return None
                # if not os.path.exists(book_dir):
                    # break

    import os

    if empty:
        from shutil import copyfile

        if not os.path.exists(book_dir):
            os.mkdir(book_dir)
        if not os.path.exists(f"{book_dir}/notebooks"):
            os.mkdir(f"{book_dir}/notebooks")

        # from importlib.resources import files
        import pkg_resources

        data_path = pkg_resources.resource_filename(__name__, "data/mask.py")
        if not os.path.exists(f"{book_dir}/notebooks/mask.py"):
            copyfile(data_path, f"{book_dir}/notebooks/mask.py")

        data_path = pkg_resources.resource_filename(__name__, "data/000_info.ipynb")
        if not os.path.exists(f"{book_dir}/notebooks/000_info.ipynb"):
            copyfile(data_path, f"{book_dir}/notebooks/000_info.ipynb")

        # data_path = files("ecoval.data").joinpath("toc.yml")
        data_path = pkg_resources.resource_filename(__name__, "data/_toc.yml")

        out = f"{book_dir}/" + os.path.basename(data_path)
        copyfile(data_path, out)

        data_path = pkg_resources.resource_filename(__name__, "data/requirements.txt")
        out = f"{book_dir}/" + os.path.basename(data_path)
        copyfile(data_path, out)

        data_path = pkg_resources.resource_filename(__name__, "data/intro.md")
        out = f"{book_dir}/" + os.path.basename(data_path)
        copyfile(data_path, out)

        # copy config

        data_path = pkg_resources.resource_filename(__name__, "data/_config.yml")
        out = f"{book_dir}/" + os.path.basename(data_path)
        # change project_title in _config.yml to title

        with open(data_path, "r") as file:
            filedata = file.read()

        # Replace the target string
        if author is not None:
            filedata = filedata.replace("author:", f"author: {author}")
        # replace title
        filedata = filedata.replace("title:", f"title: {title}")

        # Write the file out again
        with open(out, "w") as file:
            file.write(filedata)

        # copyfile(data_path, out)

        path_df = []

        # loop through the point matchups and generate notebooks

        point_paths = glob.glob("matched/point/**/**/**/**.csv")
        point_paths = [x for x in point_paths if "paths.csv" not in x]
        # loop through the paths
        for pp in point_paths:
            vv = os.path.basename(pp).split("_")[2].replace(".csv", "")
            source = os.path.basename(pp).split("_")[0]
            variable = vv
            layer = os.path.basename(pp).split("_")[1].replace(".csv", "")
            if layer != "all":
                if vv != "ph":
                    Variable = variable
                else:
                    Variable = "pH"
                if vv == "co2flux":
                    Variable = "Air-sea CO2 fluxes"
                if vv in ["poc", "doc"]:
                    Variable = Variable.upper()
                vv_file = pp
                vv_file_find = pp.replace("../../", "")

                if os.path.exists(vv_file_find):
                    if (
                        len(glob.glob(f"{book_dir}/notebooks/*point_{layer}_{variable}.ipynb"))
                        == 0
                    ):
                        file1 = pkg_resources.resource_filename(
                            __name__, "data/point_template.ipynb"
                        )
                        with open(file1, "r") as file:
                            filedata = file.read()

                        # Replace the target string
                        out = f"{book_dir}/notebooks/{source}_{layer}_{variable}.ipynb"
                        filedata = filedata.replace("point_variable", Variable)
                        filedata = filedata.replace("point_layer", layer)
                        filedata = filedata.replace("template_title", Variable)

                        # Write the file out again
                        with open(out, "w") as file:
                            file.write(filedata)
                        variable = vv
                        if variable in ["poc", "doc"]:
                            variable = variable.upper()
                        path_df.append(
                            pd.DataFrame(
                                {
                                    "variable": [variable],
                                    "path": out,
                                }
                            )
                        )


        # Loop through the gridded matchups and generate notebooks
        # identify nsbc variables in matched data
        nsbc_paths = glob.glob("matched/gridded/**/**/**.nc")
        # nsbc_paths += glob.glob("matched/gridded/**/**.nc")

        if len(nsbc_paths) > 0:
            # ds = nc.open_data("matched/gridded/nsbc/nsbc_model.nc")
            for vv in [
                os.path.basename(x).split("_")[1].replace(".nc", "") for x in nsbc_paths
            ]:
                variable = vv
                if not os.path.exists(f"{book_dir}/notebooks/nsbc_{variable}.ipynb"):
                    if variable == "ph":
                        Variable = "pH"
                    else:
                        Variable = variable
                    if variable == "co2flux":
                        Variable = "air-sea CO2 flux"
                    if variable in ["poc", "doc"]:
                        Variable = Variable.upper()
                    file1 = pkg_resources.resource_filename(
                        __name__, "data/nsbc_template.ipynb"
                    )
                    if len(glob.glob(f"{book_dir}/notebooks/*nsbc_{variable}.ipynb")) == 0:
                        with open(file1, "r") as file:
                            filedata = file.read()

                        # Replace the target string
                        filedata = filedata.replace("template_variable", variable)
                        filedata = filedata.replace("template_title", Variable)

                        # Write the file out again
                        with open(f"{book_dir}/notebooks/nsbc_{variable}.ipynb", "w") as file:
                            file.write(filedata)

                        variable = vv
                        path_df.append(
                            pd.DataFrame(
                                {
                                    "variable": [variable],
                                    "path": [f"{book_dir}/notebooks/nsbc_{variable}.ipynb"],
                                }
                            )
                        )

        # figure out if mld needs to be calculated...

        mld_paths = glob.glob("matched/point/**/all/temperature/**temperature**.csv")

        if len(mld_paths) > 0:

            if not os.path.exists(f"{book_dir}/notebooks/temperature_mld.ipynb"):
                file1 = pkg_resources.resource_filename(__name__, "data/mld_template.ipynb")
                with open(file1, "r") as file:
                    filedata = file.read()

                # Replace the target string
                filedata = filedata.replace("template_variable", "temperature")
                filedata = filedata.replace("template_title", "Mixed layer depth")

                # Write the file out again
                with open(f"{book_dir}/notebooks/temperature_mld.ipynb", "w") as file:
                    file.write(filedata)

                path_df.append(
                    pd.DataFrame(
                        {
                            "variable": ["temperature"],
                            "path": [f"{book_dir}/notebooks/temperature_mld.ipynb"],
                        }
                    )
                )


        # loop through all notebooks and replace paths

        i = 0

        # need to start by figuring out whether anything has already been run...

        i = 0

        for ff in [x for x in glob.glob("{book_dir}/notebooks/*.ipynb") if "info" not in x]:
            try:
                i_ff = int(os.path.basename(ff).split("_")[0])
                if i_ff > i:
                    i = i_ff
            except:
                pass

        i_orig = i

        if len(path_df) > 0:
            path_df = pd.concat(path_df)
            path_df = path_df.sort_values("variable").reset_index(drop=True)

        for i in range(len(path_df)):
            file1 = path_df.path.values[i]
            # pad i with zeros using zfill
            i_pad = str(i + 1).zfill(3)
            new_file = (
                os.path.dirname(file1) + "/" + i_pad + "_" + os.path.basename(file1)
            )
            os.rename(file1, new_file)
            # print(key, value)

        # copy the summary.ipynb notebook and add i_pad to the name

        i = i + 2
        i_pad = str(i).zfill(3)

        shelf = False
        # figure out if we need the shelf
        try:
            ds_regions = nc.open_data(f"{data_dir}/amm7_val_subdomains.nc")
            ds_xr = ds_regions.to_xarray()
            lon_size = len(ds_xr.lon)
            lat_size = len(ds_xr.lat)

            ensemble = nc.create_ensemble("matched")
            ff = ensemble[0]
            ds = nc.open_data(ff)
            ds_xr = ds.to_xarray()
            lon_size_ds = len(ds_xr.lon)
            lat_size_ds = len(ds_xr.lat)

            if lon_size_ds == lon_size:
                if lat_size_ds == lat_size:
                    shelf = True
                else:
                    shelf = False
        except:
            shelf = False

        # copy the summary notebook for the full domain

        if shelf:
            file1 = pkg_resources.resource_filename(__name__, "data/summary.ipynb")
            if len(glob.glob(f"{book_dir}/notebooks/*summary.ipynb")) == 0:
                copyfile(file1, f"{book_dir}/notebooks/{i_pad}_summary_shelf.ipynb")
                # change domain_title to "Shelf"
                with open(f"{book_dir}/notebooks/{i_pad}_summary_shelf.ipynb", "r") as file:
                    filedata = file.read()

                # Replace the target string
                filedata = filedata.replace("domain_title", "Shelf")
                # replace shelf_mask with True
                filedata = filedata.replace("shelf_mask", "True")

                # Write the file out again
                with open(f"{book_dir}/notebooks/{i_pad}_summary_shelf.ipynb", "w") as file:
                    file.write(filedata)

                i += 1

                i_pad = str(i).zfill(3)

        file1 = pkg_resources.resource_filename(__name__, "data/summary.ipynb")
        if len(glob.glob(f"{book_dir}/notebooks/*summary.ipynb")) == 0:
            copyfile(file1, f"{book_dir}/notebooks/{i_pad}_summary.ipynb")
        else:
            if i > (i_orig + 1):
                initial = glob.glob(f"{book_dir}/notebooks/*summary.ipynb")[0]
                copyfile(initial, f"{book_dir}/notebooks/{i_pad}_summary.ipynb")
                i += 1

        # change domain_title to "Full domain"

        with open(f"{book_dir}/notebooks/{i_pad}_summary.ipynb", "r") as file:
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("domain_title", "Full domain")
        # replace shelf_mask with False
        filedata = filedata.replace("shelf_mask", "False")

        # Write the file out again
        with open(f"{book_dir}/notebooks/{i_pad}_summary.ipynb", "w") as file:
            file.write(filedata)

        # pair the notebooks using jupyter text

        os.system(f"jupytext --set-formats ipynb,py:percent {book_dir}/notebooks/*.ipynb")

        # add the chunks
        add_chunks()

        # sync the notebooks
        #
        os.system(f"jupytext --sync {book_dir}/notebooks/*.ipynb")

    #        return None

    # return None

    # loop through notebooks and change fast_plot_value to fast_plot

    for ff in glob.glob(f"{book_dir}/notebooks/*.ipynb"):
        with open(ff, "r") as file:
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("fast_plot_value", str(fast_plot))

        # Write the file out again
        with open(ff, "w") as file:
            file.write(filedata)

    # fix the toc using the function

    # raise ValueError("here")
    fix_toc(book_dir)

    os.system(f"jupyter-book build {book_dir}/")

    import os

    stamps = [os.path.basename(x) for x in glob.glob(f"{book_dir}/notebooks/.trackers/*")]
    stamps.append("nctoolkit_rwi_uhosarcenctoolkittmp")

    delete = []
    for x in stamps:
        delete += glob.glob("/tmp/*" + x + "*")

    for ff in delete:
        if os.path.exists(ff):
            if "nctoolkit" in x:
                os.remove(ff)
    webbrowser.open("file://" + os.path.abspath(f"{book_dir}/_build/html/index.html"))


try:
    from importlib.metadata import version as _version
except ImportError:
    from importlib_metadata import version as _version

try:
    __version__ = _version("ecoval")
except Exception:
    __version__ = "999"
