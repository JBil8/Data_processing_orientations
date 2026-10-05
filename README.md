# Data_processing_orientations

Post-processing code for the orientation statistics of non-spherical granular
particles (ellipsoids and rods) under simple shear, extracted from
LAMMPS/Liggghts DEM simulations.

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
│   ├── Jeffrey_orbits.ipynb         # Jeffrey-orbit comparison, ODF fits
│   └── abel_transform_raw_data.ipynb
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
| `-d` | path to the raw simulation data (default: local LAMMPS output root) |
| `-p` | *disables* full processing and loads the exported pickle instead |

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

## Citation

If you use this code or the dataset, please cite both (see `CITATION.cff`).

## License

Code: [GPL-3.0](LICENSE). Dataset: Creative Commons Attribution 4.0.
