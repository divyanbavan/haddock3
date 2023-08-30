"""HADDOCK3 module for alanine scan."""
from pathlib import Path
import os
import numpy as np
import pandas as pd
from haddock import log
from haddock.libs.libontology import ModuleIO, TopologyFile
from haddock.libs.libsubprocess import CNSJob
from haddock.modules import get_engine
from haddock.modules import BaseHaddockModule
from haddock.modules.analysis.alascan.scan import mutate, add_delta_to_bfactor
from functools import partial
import shutil
from haddock.libs.libutil import parse_ncores
from haddock.modules.analysis.alascan.scan import (
    Scan,
    ScanJob,
    add_delta_to_bfactor,
    alascan_cluster_analysis,
)
from haddock.libs.libparallel import Scheduler
import plotly.graph_objects as go


RECIPE_PATH = Path(__file__).resolve().parent
DEFAULT_CONFIG = Path(RECIPE_PATH, "defaults.yaml")


def get_index_list(nmodels, ncores):
    """Optimal distribution of models among cores"""
    spc = nmodels // ncores
    # now the remainder
    rem = nmodels % ncores
    # now the list of indexes to be used for the RMSD calculation
    index_list = [0]
    for core in range(ncores):
        if core < rem:
            index_list.append(index_list[-1] + spc + 1)
        else:
            index_list.append(index_list[-1] + spc)
    return index_list

def make_alascan_plot(df, clt_id, scan_res = "ALA"):
    """
    Makes a plotly interactive plot.

    Score components are here **weighted** by their respective
    contribution to the total score.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the results of the alanine scan.
    clt_id : int
        Cluster ID.
    scan_res : str, optional
        Residue name used for the scan, by default "ALA"
    """
    plot_name = f"scan_clt_{clt_id}"
    log.info(f"Generating {scan_res} scanning plot {plot_name}")

    # create figure
    fig = go.Figure(layout={"width": 2000, "height": 1000})
    fig.add_trace(
        go.Bar(
            x=df["full_resname"],
            y=df["delta_score"],
            name="delta_score",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["full_resname"],
            y=df["delta_vdw"],
            name="delta_vdw",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["full_resname"],
            y=0.2*df["delta_elec"],
            name="delta_elec",
        )
    )

    fig.add_trace(
        go.Bar(
            x=df["full_resname"],
            y=df["delta_desolv"],
            name="delta_desolv",
        )
    )
    # prettifying layout
    fig.update_layout(
         title= f"{scan_res} scanning cluster {clt_id}",
         xaxis=dict(
             title="Residue Name",
             tickfont_size=14,
             titlefont_size=16,
             tick0=df["full_resname"],
             #dtick=10,
         ),
         yaxis=dict(
             title="Weigted delta",
             titlefont_size=16,
             tickfont_size=14,
         ),
         legend=dict(x=1.01, y=1.0, font_family="Helvetica", font_size=16),
         barmode="group",
         bargap=0.05,
         bargroupgap=0.05,
         hovermode="x unified",
         hoverlabel=dict(font_size=16, font_family="Helvetica"),
     )
    # save html
    html_output_filename = f"{plot_name}.html"
    fig.write_html(html_output_filename)


class HaddockModule(BaseHaddockModule):
    """HADDOCK3 module for alanine scan."""

    name = RECIPE_PATH.name

    def __init__(self, order, path, *ignore, init_params=DEFAULT_CONFIG,
                 **everything):
        super().__init__(order, path, init_params)

    @classmethod
    def confirm_installation(cls):
        """Confirm if module is installed."""
        return

    def _run(self):
        """Execute module."""

        # Get the models generated in previous step
        try:
            models = self.previous_io.retrieve_models(individualize=True)
        except Exception as e:
            self.finish_with_error(e)

        # Parallelisation : optimal dispatching of models
        nmodels = len(models)
        ncores = parse_ncores(n=self.params['ncores'], njobs=nmodels)

        log.info(f"Running on {ncores} cores")

        index_list = get_index_list(nmodels, ncores)

        alascan_jobs = []
        for core in range(ncores):
            output_name = "alascan_" + str(core) + ".scan"
            contact_obj = Scan(
                model_list=models[index_list[core]:index_list[core + 1]],
                output_name=output_name,
                core=core,
                path=Path("."),
                params=self.params,
                )
            # running now the ContactJob
            job_f = Path(output_name)
            # init RMSDJob
            job = ScanJob(
                job_f,
                self.params,
                contact_obj,
                )
            alascan_jobs.append(job)

        contact_engine = Scheduler(alascan_jobs, ncores=ncores)
        contact_engine.run()
        # check if all the jobs have been completed
        alascan_file_l = []
        not_found = []
        for job in alascan_jobs:
            if not job.output.exists():
                not_found.append(job.output.name)
                wrn = f'Alascan not completed for {job.output.name}'
                log.warning(wrn)
            else:
                alascan_file_l.append(str(job.output))

        if not_found:
            # Not all alascan were executed, cannot proceed
            self.finish_with_error("Several alascan files were not generated:"
                                   f" {not_found}")
        
        # cluster-based analysis
        clt_alascan = alascan_cluster_analysis(models)
 
        # now plot the data
        if self.params["plot"] is True:
            for clt_id in clt_alascan:
                scan_clt_filename = f"scan_clt_{clt_id}.csv"
                df_scan_clt = pd.read_csv(scan_clt_filename, sep="\t", comment="#")
                # plot the data
                plot_name = f"scan_clt_{clt_id}"
                try:
                    make_alascan_plot(df_scan_clt, clt_id, self.params['scan_residue'])
                except Exception as e:
                    log.warning(
                        "Could not create interactive plot. The following error"
                        f" occurred {e}"
                    )
        # if output is true, write the models and export them
        if self.params["output"] is True:
            models_to_export = []
            for model in models:
                name = f"{model.file_name}_alascan.pdb"
                # changing attributes
                name_path = Path(name)
                # TODO: change this
                # name_path.write_text(model.rel_path.read_text())
                shutil.copy(model.rel_path, name_path)

                alascan_fname = f"scan_{model.file_name}.csv"
                # add delta_score as a bfactor to the model
                df_scan = pd.read_csv(alascan_fname, sep="\t", comment="#")
                add_delta_to_bfactor(name, df_scan)
                model.ori_name = model.file_name
                model.file_name = name
                model.full_name = name
                model.rel_path = Path('..', Path(self.path).name, name)
                model.path = str(Path(self.path).resolve())
                models_to_export.append(model)
            self.output_models = models_to_export
        
        else:
            # Send models to the next step,
            #  no operation is done on them
            self.output_models = models
        self.export_output_models()



            
            

        
