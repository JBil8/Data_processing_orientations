# Data_processing_orientations

Post-processing code for the orientation statistics of non-spherical granular
particles (ellipsoids and rods) under simple shear, extracted from Liggghts DEM simulations.

The pipeline computes particle orientation distributions, nematic order
parameter (Maier–Saupe / ODF fits), Jeffrey-orbit comparison, rotational
diffusion, stress–orientation coupling, and related time-series statistics.

## Repository structure

```
.
├── main_orientations.py             # main post-processing pipeline (CLI entry point)
├── maier_3d.ipynb                   # Maier–Saupe / ODF analysis notebook
├── parallel_processing_sbatch_I.sh  # SLURM parametric sweep over cof × ap × I
├── src/                             # processing modules
│   ├── DataReader.py, DataProcessor.py  # abstract base classes
│   ├── ReaderVtk.py, ReaderDump.py      # readers for VTK / dump output files
│   ├── ProcessorVtk.py, ProcessorDump.py,
│   ├── ProcessorCsv.py, ProcessorDat.py # per-time-step processing
│   ├── CombinedProcessor.py
│   ├── DataExporter.py                  # pickle/CSV export of aggregated results
│   ├── DataPlotter.py, histogram_utils.py
│   └── script_vtk_to_binary.py, rename_binary_vtk.sh  # raw-data utilities
├── notebooks/
│   └── abel_transform_raw_data.ipynb
├── simulation_runners/              # LIGGGHTS input scripts, SLURM runner, source patch
│   ├── in.simple_shear_le_orientation
│   ├── in.insertion
│   ├── script_simple_shear_orientation.sh
│   └── pair_gran_base_delta.patch
├── dataset_description.md           # structure of the processed pkl datasets
└── data/                            # generated outputs + reference CSVs
```

The pipeline modules live in `src/` and are imported by
`main_orientations.py` through a `sys.path` bootstrap; the CLI is run from the
repository root. `data/` holds all generated outputs (git-ignored) plus the
small reference CSVs loaded by the notebooks (`r_talbot.csv`, `s_talbot.csv`,
`thetax_ap_*.csv`).

## Installation

Requires Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the full post-processing pipeline from the repository root:

```bash
python main_orientations.py -c 0.4 -a 3.0 -v 0.1 -s 50 -np 8
```

Arguments:

| Flag | Meaning |
|------|---------|
| `-c` | inter-particle coefficient of friction |
| `-a` | particle aspect ratio (long/small axis) |
| `-v` | Inertial number (or packing fraction, depending on simulation type) |
| `-s` | geometric parameter `s` recorded in the raw-data directory name |
| `-np` | number of parallel processes (default 8) |
| `-d` | path to the raw simulation data — **required for the full processing** |
| `-p` | *disables* full processing and loads the exported pickle instead |

Diagnostic plots are saved to `Figures/`. The post-processing sweep script
`parallel_processing_sbatch_I.sh` submits SLURM jobs over
friction × aspect ratio × Inertial number; set the raw-data directory in the
`RAW_DIR` variable at the top of the script.

The pipeline expects raw simulation directories named
`alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/` containing the VTK snapshots, the
contact-data dump files, and the shear-rate CSV exported by the simulation.
Results are exported to
`data/output_data_hertz/orientation_simple_shear_ap{ap}_cof_{cof}_I_{I}.pkl`.
The structure of the exported pickles (keys, shapes, normalisations) is
documented in `dataset_description.md`.

The processed datasets used in the publication are available on Zenodo
(DOI: 10.5281/zenodo.XXXXXXX — to be inserted upon publication).

Legacy notebooks and exploratory scripts are preserved on the
[`archive/legacy-main`](../../tree/archive/legacy-main) branch.

## Simulations (LIGGGHTS)

The raw simulation data are not distributed, but the tools to generate them
are included in `simulation_runners/`:

- `in.simple_shear_le_orientation` — LIGGGHTS input script for the simple
  shear runs (superquadric ellipsoids, Lees–Edwards-style shearing,
  pressure-controlled via `pressure_target`).
- `in.insertion` — polydisperse particle insertion, `include`d by the input
  script (path passed by the runner as the `insertion_script` variable).
- `script_simple_shear_orientation.sh` — SLURM runner looping over
  friction × aspect ratio × Inertial number. Edit the variables at the top
  (`executable`, `run_root`, parameter arrays), then submit. It creates the
  run directories `alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/` and runs
  LIGGGHTS inside them, so the outputs can be post-processed directly with
  `-d <run_root>`.
- `pair_gran_base_delta.patch` — patch for the LIGGGHTS source
  (`src/pair_gran_base.h`): it moves the assignment of the contact overlap
  vector `sidata.delta` to *after* the `surfacesIntersect` calls, so the
  contact model and the `pair/gran/local` compute see the correct overlap.
  Apply it once in your LIGGGHTS checkout before compiling:

  ```bash
  cd LIGGGHTS-PUBLIC/src
  git apply /path/to/pair_gran_base_delta.patch   # or: patch -p1 < ...
  make -j
  ```

## Citation

If you use this code or the dataset, please cite both (see `CITATION.cff`).

## License

Code: [GPL-3.0](LICENSE). Dataset: Creative Commons Attribution 4.0.
