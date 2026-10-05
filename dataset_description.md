# Processed simulation datasets — description

Processed outputs of the post-processing pipeline in
[Data_processing_orientations](https://github.com/JBil8/data_processing_orientations)
(v1.0.0) applied to Liggghts DEM simulations of monodisperse granular
ellipsoids under steady simple shear. The dataset contains the aggregated
per-run results (Python `pickle` files) used to produce all figures of the
associated publication.

All dimensional quantities (stresses, velocities, shear rates, times) are in
the reduced simulation units of the underlying DEM runs.

## 1. Dataset layout

| Path | Content |
|---|---|
| `output_data_hertz/` | main dataset: 127 pickles, `orientation_simple_shear_ap{a}_cof_{c}_I_{I}.pkl` |
| `output_data_e0.9/` | 4 pickles — restitution coefficient 0.9 |
| `output_data_high_kappa/` | 4 pickles — higher stiffness number, kappa = 4.6e5 |
| `output_data_mono/` | 112 pickles — monodisperse particles |
| `output_data_N4000/` | 4 pickles — 4000 particles |
| `output_data_rods/` | 27 pickles — rod-like particles |
| `output_data_volume/` | 8 pickles — volume-controlled (fixed packing) instead of pressure-controlled |
| `output_data_hertz/U_and_rmse_self_consistent.pkl` (and `_rods`/`_volume` variants) | stacked self-consistent Maier–Saupe fit results |

All `orientation_simple_shear_*.pkl` files across all directories share the
identical format (48 keys, documented in section 2). The variant directories
are subsets covering a reduced parameter range, with one control parameter of
the simulation changed (see table below); `output_data_hertz/` contains the
full sweep. The pickles are read by `maier_3d.ipynb` in the code repository.

### File naming and parameter coverage

Each file name encodes the control parameters of the simulation it
aggregates (the raw data lived in directories named
`alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/`):

- **`ap`** — particle aspect ratio (long/small semi-axis), `> 1`
  (prolate ellipsoids; in `output_data_rods/` rod-like particles).
- **`cof`** — inter-particle coefficient of friction.
- **`I`** — Inertial number.

Coverage:

| Directory | `ap` | `cof` | `I` |
|---|---|---|---|
| `output_data_hertz/` | 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 9.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 1.0, 10.0, 100.0 | 0.1 (119 runs), 0.01 (8 runs) |
| `output_data_e0.9/` | 5.0 | 0.0, 0.01, 0.4, 10.0 | 0.1 |
| `output_data_high_kappa/` | 5.0 | 0.0, 0.01, 0.4, 10.0 | 0.1 |
| `output_data_mono/` | 1.2 – 8.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 1.0, 10.0, 100.0 | 0.1 |
| `output_data_N4000/` | 5.0 | 0.0, 0.01, 0.4, 10.0 | 0.1 |
| `output_data_rods/` | 2.0, 3.3, 5.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 0.7, 1.0, 10.0, 100.0 | 0.1 |
| `output_data_volume/` | 5.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 1.0, 10.0, 100.0 | 0.1 |

Not every parameter combination is present in `output_data_hertz/`; a
combination is missing if the simulation or the fit did not converge.

## 2. `orientation_simple_shear_*.pkl` (48 keys, identical everywhere)

One pickle per run. Scalars unless noted.

### Simulation / macroscopic state
| Key | Meaning |
|---|---|
| `inertialNumber`, `shear_rate` | Inertial number; imposed shear rate `gamma_dot` |
| `phi`, `phi_fluct` | packing fraction; its per-timestep fluctuation |
| `press`, `press_fluct` | pressure; fluctuation |
| `p_yy`, `p_xy`, `p_yy_fluct`, `p_xy_fluct` | normal / shear stress components; fluctuations |
| `Nx_diff`, `Nz_diff`, `..._fluct` | flow-alignment (nematic) differences along x and z; fluctuations |
| `msdZ`, `msdZ_fluct` | mean-square displacement along z; fluctuation |
| `Dyy`, `Dzz` | diffusion coefficients (y: vorticity, z: gradient) |

### Orientation statistics / Maier–Saupe fits
| Key | Meaning |
|---|---|
| `bin_centers`, `f_data` (100,) | ODF: angle bin centres in the shear plane and measured probability density `p(theta)` |
| `U_fitted`, `rmse_fit` | fitted Maier–Saupe potential strength `U` and fit RMSE |
| `S2_scalar`, `S4_scalar` | uniaxial nematic order parameters (2nd/4th rank) |
| `biaxiality` | biaxiality parameter |
| `director`, `theta_d` | director vector; its in-plane angle |
| `eigenvalues` (3,), `eigenvectors` (3,3) | of the nematic tensor; largest eigenvalue's eigenvector = director |
| `nematic_tensor` (3,3), `S4` (3,3,3,3) | raw rank-2 and rank-4 order tensors |
| `screening_jeffrey`, `error_screening` | Jeffrey-orbit screening factor and its error |
| `ave_omega` (3,) | mean angular velocity — **stored double-normalised: raw `<omega> = ave_omega * shear_rate**2`** |
| `theta_bins` (15,), `omega_bins` (15,), `std_omega_bins` (15,) | binned `<omega_z>/gamma_dot` (mean and SEM) over 15 angle bins in `[-pi/2, pi/2]` (`theta_bins` = bin centres) — comparable with the Jeffrey prediction `-[1 - beta cos(2 theta)]/2` |

### Time series and correlations
| Key | Meaning |
|---|---|
| `times` (500,), `oacf` (500,) | orientation autocorrelation function vs lag time |
| `D_r`, `Pe`, `tau_r`, `A_infty` | rotational diffusion fitted from the OACF; Peclet number; rotational relaxation time; long-time OACF plateau |
| `S2_over_time`, `strains` (3001,) | order parameter vs accumulated strain |
| `angle_over_time`, `biaxility_over_time` (3001,) | director angle / biaxiality vs accumulated strain |

## 3. `U_and_rmse_self_consistent*.pkl`

Stacked results of the self-consistent Maier–Saupe analysis (axes ordered as
written by `maier_3d.ipynb`):

| File | Shape | Axes |
|---|---|---|
| `output_data_hertz/U_and_rmse_self_consistent.pkl`, `output_data_mono/…` | (8, 1, 14) | `(i_cof, i_I, i_ap)` — 8 friction coefficients × 1 Inertial number × 14 aspect ratios |
| `output_data_rods/U_and_rmse_self_consistent_rods.pkl` | (3, 1, 3) | 3 friction coefficients × 1 Inertial number × 3 aspect ratios |
| `output_data_volume/U_and_rmse_self_consistent_volume.pkl` | (8, 1, 1) | 8 friction coefficients × 1 Inertial number × 1 aspect ratio |

Keys: `U1_self_consistents`, `U2_self_consistents` (fitted potential
strengths), `rmse_self_consistents` (fit residuals).

## 4. Loading the data

```python
import pickle

with open("output_data_hertz/orientation_simple_shear_ap3.0_cof_1.0_I_0.1.pkl", "rb") as f:
    d = pickle.load(f)
odf_angle, odf_p = d["bin_centers"], d["f_data"]
```

The notebooks in the repository show the full reading logic
(`read_pdf_theta` in `maier_3d.ipynb`).

## 5. Regeneration

Raw simulation data are not included in this dataset. The pickles are
regenerated from raw Liggghts output with:

```bash
python main_orientations.py -c 0.4 -a 3.0 -v 0.1 -s 50 -np 8
# -> data/output_data_hertz/orientation_simple_shear_ap3.0_cof_0.4_I_0.1.pkl
```

The Liggghts input scripts, the SLURM runner, and the source patch needed to
generate the raw data are part of the code repository
(`simulation_runners/`).

## 6. License and citation

- Dataset: Creative Commons Attribution 4.0 (CC-BY-4.0).
- Code: GPL-3.0 — <https://github.com/JBil8/data_processing_orientations>.
- Please cite both; see `CITATION.cff` in the code repository.
