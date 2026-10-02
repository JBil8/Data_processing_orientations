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
  `output_data_hertz/`). Args: `-c` cof, `-a` aspect ratio, `-v` Inertial number,
  `-s` pressure slot, `-np` processes (default 8), `-d/--input_dir` path to raw data.
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
  `DataExporter` to `output_data_hertz/orientation_simple_shear_ap{ap}_cof_{cof}_I_{I}.pkl`.
- `DataProcessor.py` is the tiny base class of all `Processor*` modules — do not delete it.

## Notebooks
- Only three remain: `Jeffrey_orbits.ipynb`, `maier_3d.ipynb`,
  `abel_transform_raw_data.ipynb` (outputs stripped).
- `Jeffrey_orbits.ipynb` loads old-named pkls from relative `output_data_final/`;
  `maier_3d.ipynb` loads from `output_data_hertz/`. Both pkl families ship in the
  Zenodo dataset (DOI placeholders in `README.md`/`CITATION.cff`).

## Known bugs / traps
- Fixed on `publication-prep` branch: `DataExporter.import_with_pickle()` `'wb'`
  mode and the undefined `simulation_type`/`plotter` in the `-p` branch.
  Verify the fix is merged before relying on `-p`.

## Conventions
- Git tracks code only: `.gitignore` excludes all data/artifacts
  (`*.pkl *.csv *.png *.pdf *.svg *.npy *.zip *.tar.gz`) and `output_data_*` /
  `inertial_dir_*` / `Alpha_*`. Never commit data outputs.
- Exception: small reference CSVs (`thetax_ap_*.csv`, `r_talbot.csv`,
  `s_talbot.csv`) are force-added — notebooks load them directly.
- Plot variants use filename suffixes `_mono`, `_rods`.
- Commits: short imperative summaries directly on `main` (no PR flow).
- Dataset/citation metadata: `CITATION.cff`, `.zenodo.json` (Zenodo–GitHub
  integration; placeholders `10.5281/zenodo.XXXXXXX` / `YYYYYYY` must be filled).
