# AGENTS.md

Research post-processing of LAMMPS/Liggghts DEM simulations (sheared granular
ellipsoids/rods): orientation statistics, Jeffrey orbits, Maier–Saupe / ODF fits.
No tests, no lint/CI — verification is running the script or notebook cells.

## Environment
- Python 3.12 venv at `.venv/`; deps pinned in `requirements.txt`
  (scipy, numpy, matplotlib, vtk, pandas). `vtk` is imported at module load — always required.
- `nbconvert` is not installed; strip notebook outputs with a direct JSON script if needed.

## Running
- Entry point: `main_orientations.py` from repo root (outputs go to relative
  `data/output_data_hertz/`). Processing modules live in `src/` (added to
  `sys.path` by the bootstrap at the top of `main_orientations.py`). Args:
  `-c` cof, `-a` aspect ratio, `-v` Inertial number, `-s` pressure slot,
  `-np` processes (default 8), `-d/--input_dir` path to raw data.
- Full pipeline: `python main_orientations.py -c 0.4 -a 3.0 -v 0.1 -s 50 -np 8`
- **Flags are inverted**: `-p` (`--postprocess`) *disables* full processing
  (`action='store_false'`) and loads the exported pickle instead; same for `-cw`.
- Raw input data is **outside this repo**; `-d` defaults to
  `~/Documents/phd_research/Liggghts_simulations/cluster_simulations/` (cluster
  paths commented in `main_orientations.py`). Data dirs follow
  `alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/`.
- Parametric sweeps: `parallel_processing_sbatch_I.sh` submits SLURM jobs over
  cof × ap × I (8 CPUs each, max 10 parallel). It passes `-s 50` (or `50*ap` if ap<1)
  into the `pressure` arg — that slot holds the geometric parameter `s`, not a pressure.

## Pipeline
- `ReaderVtk`/`ReaderDump` (base `DataReader`) → `ProcessorVtk` + `ProcessorDump`
  combined in `CombinedProcessor.process_single_step` → run via
  `multiprocessing.Pool` → aggregated by `process_results()` → exported by
  `DataExporter` to
  `data/output_data_hertz/orientation_simple_shear_ap{ap}_cof_{cof}_I_{I}.pkl`.
- All processing modules are in `src/` and import each other flatly
  (`from DataProcessor import …`); `DataProcessor.py` is the tiny base class
  of all `Processor*` modules — do not delete it.

## Notebooks
- `main_orientations.py` + `maier_3d.ipynb` stay in the repo root;
  `Jeffrey_orbits.ipynb` and `abel_transform_raw_data.ipynb` are in `notebooks/`
  (outputs stripped). Notebooks import no local modules.
- `Jeffrey_orbits.ipynb` loads old-named pkls from relative `data/output_data_final/`;
  `maier_3d.ipynb` loads from `data/output_data_hertz/` and the reference CSVs
  from `data/`. Both pkl families ship in the Zenodo dataset
  (DOI placeholders in `README.md`/`CITATION.cff`); the pkl key/shape
  reference is `dataset_description.md`.

## Known bugs / traps
- Fixed and merged on `main`: `DataExporter.import_with_pickle()` `'wb'` mode,
  the legacy pkl filename it searched for, and the undefined
  `simulation_type`/`plotter` in the `-p` branch.

## Conventions
- Git tracks code only: `.gitignore` excludes all data/artifacts by extension
  (`*.pkl *.csv *.png *.pdf *.svg *.npy *.zip *.tar.gz`) plus a blanket `data/`
  ignore. Never commit data outputs.
- Exception: small reference CSVs (`data/thetax_ap_*.csv`, `data/r_talbot.csv`,
  `data/s_talbot.csv`) are tracked — notebooks load them directly.
- Plot variants use filename suffixes `_mono`, `_rods`.
- Commits: short imperative summaries directly on `main` (no PR flow).
- Legacy notebooks/scripts live on the `archive/legacy-main` branch.
- Dataset/citation metadata: `CITATION.cff`, `.zenodo.json` (Zenodo–GitHub
  integration; placeholders `10.5281/zenodo.XXXXXXX` / `YYYYYYY` must be filled).
