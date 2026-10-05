# Processed simulation datasets — description

Processed outputs of the post-processing pipeline in
[Data_processing_orientations](https://github.com/JBil8/data_processing_orientations)
(v1.0.0) applied to LAMMPS/Liggghts DEM simulations of monodisperse granular
ellipsoids under steady simple shear. The dataset contains the aggregated
per-run results (Python `pickle` files) used to produce all figures of the
associated publication.

All dimensional quantities (stresses, velocities, shear rates, times) are in
the reduced simulation units of the underlying DEM runs.

## 1. Dataset layout

| Path | Content |
|---|---|
| `output_data_final/` | 637 pickles from the older pipeline, `simple_shear_ap{a}_cof_{c}_I_{I}.pkl` — read by `Jeffrey_orbits.ipynb` |
| `output_data_hertz/` | 127 pickles from the current (Hertzian-contact) pipeline, `orientation_simple_shear_ap{a}_cof_{c}_I_{I}.pkl` — read by `maier_3d.ipynb` |
| `output_data_hertz/U_and_rmse_self_consistent.pkl` | stacked self-consistent Maier–Saupe fit results |

### File naming and parameter coverage

Each file name encodes the three control parameters of the simulation it
aggregates (the raw data lived in directories named
`alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/`):

- **`ap`** — particle aspect ratio (long/small semi-axis). In
  `output_data_final/` values `ap < 1` denote oblate/flattened ellipsoids,
  recorded as the small/large ratio (equivalent aspect ratio `1/ap`); in
  `output_data_hertz/` all values are `> 1` (prolate ellipsoids).
- **`cof`** — inter-particle coefficient of friction `mu_p`.
- **`I`** — Inertial number.

Coverage:

| Family | `ap` | `cof` | `I` |
|---|---|---|---|
| `output_data_final/` | 0.33, 0.4, 0.5, 0.56, 0.67, 0.83, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 1.0, 10.0 | 0.001, 0.0022, 0.0046, 0.01, 0.022, 0.046, 0.1 |
| `output_data_hertz/` | 1.2 – 9.0 | 0.0, 0.001, 0.01, 0.1, 0.4, 1.0, 10.0, 100.0 | 0.1 |

Not every parameter combination is present; a combination is missing if the
simulation or the fit did not converge.

## 2. `output_data_hertz/orientation_simple_shear_*.pkl` (48 keys)

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

## 3. `output_data_final/simple_shear_*.pkl` (older pipeline)

One pickle per run; key availability varies slightly between files (a few
keys, e.g. `D_rot` or `auto_corr`, are `None`/absent for runs with
insufficient statistics).

### Orientation / dynamics
| Key | Meaning |
|---|---|
| `pdf_thetax`, `pdf_thetaz` (180, 2) | column 0 = angle (deg), column 1 = probability density of the in-plane tilt `theta_x` / of `theta_z` — read by `Jeffrey_orbits.ipynb` |
| `percent_aligned`, `S2` | fraction of aligned particles; uniaxial order parameter |
| `Omega_x`, `Omega_y`, `Omega_z` | mean angular velocity components (raw, not normalised: `Omega_z/gamma_dot ≈ -0.5`) |
| `omega_fluctuations` (3,), `vx/vy/vz_fluctuations` | fluctuations of angular / linear velocities |
| `D_rot` | rotational diffusion coefficient |
| `auto_corr` (100,), `strain` (100,) | orientation autocorrelation vs accumulated strain |
| `thetax_mean`, `thetaz_mean` | mean tilt angles |

### Micro-macro quantities
| Key | Meaning |
|---|---|
| `stress_contacts` (3,3), `fabric` (3,3) | contact stress tensor; contact fabric tensor |
| `Z`, `percent_sliding` | coordination number; fraction of sliding contacts |
| `tke`, `rke` | total kinetic energy (translational/rotational) |
| `c_delta_vy` (18,), `c_r_values` (18,) | velocity correlation vs pair separation |
| `box_x_length`, `box_y_length`, `box_z_length` | simulation box dimensions |
| `muI_dissipation`, `ratio_diss_measurement`, `total_normal_dissipation`, `total_tangential_dissipation` | frictional dissipation measures |
| `area_adjustment_ellipsoid` (10,), `total_area` | ellipsoid cross-section correction for contact statistics |

### Chunk profiles (8 spatial bins)
From LAMMPS chunk output (reader columns: `timestep, bin_index, coord, Ncount,
vx, vy, vz, c_omegaz, density_mass, v_pxx_loc, v_pyy_loc, v_pzz_loc,
v_pxy_loc`), time-averaged over the steady state; `_avg` = time mean,
`_std_dev` = time standard deviation, per bin:

| Key | Meaning |
|---|---|
| `bins` (8,) | bin coordinates |
| `vx_avg/_std_dev`, `vy_...`, `vz_...` (8,) | velocity profile |
| `c_omegaz_avg/_std_dev` (8,) | mean angular velocity z-component profile |
| `coord_avg/_std_dev`, `Ncount_avg/_std_dev` (8,) | coordination number; contacts per bin |
| `density_mass_avg/_std_dev` (8,) | mass density profile |
| `v_pxx_loc_avg/_std_dev`, `v_pyy_...`, `v_pzz_...`, `v_pxy_...` (8,) | local stress components |

### Force/contact histograms
| Key | Meaning |
|---|---|
| `contacts_hist_global_normal/tangential` (144,), `contacts_hist_cont_point_global` (144,) | global contact-force histograms (144 bins) |
| `global_normal_force_hist`, `global_tangential_force_hist` (144,) | force histograms weighted by force |
| `contacts_hist_cont_point_local` (10,), `local_normal_force_hist_cp`, `local_tangential_force_hist_cp` (10,) | local (contact-point) histograms |
| `bin_counts_power`, `power_dissipation_normal/tangential` (10,) | dissipated power per bin |
| `normal_force_hist_mixed`, `tangential_force_hist_mixed` (100,) | mixed-branch force histograms |
| `max_vx_diff` | maximum deviation of `vx` from linear profile |

## 4. `output_data_hertz/U_and_rmse_self_consistent.pkl`

Stacked results of the self-consistent Maier–Saupe analysis (axes ordered as
written by `maier_3d.ipynb`):

| Key | Shape | Axes |
|---|---|---|
| `U1_self_consistents`, `U2_self_consistents`, `rmse_self_consistents` | (8, 1, 14) | `(i_cof, i_I, i_ap)` — 8 friction coefficients × 1 Inertial number × 14 aspect ratios |

## 5. Loading the data

```python
import pickle

# current pipeline (one file per run)
with open("output_data_hertz/orientation_simple_shear_ap3.0_cof_1.0_I_0.1.pkl", "rb") as f:
    d = pickle.load(f)
odf_angle, odf_p = d["bin_centers"], d["f_data"]

# older pipeline (ODF used by Jeffrey_orbits.ipynb)
with open("output_data_final/simple_shear_ap3.0_cof_10.0_I_0.1.pkl", "rb") as f:
    d_old = pickle.load(f)
theta, p_theta = d_old["pdf_thetax"][:, 0], d_old["pdf_thetax"][:, 1]
```

The notebooks in the repository show the full reading logic
(`read_pdf_theta` in `maier_3d.ipynb`, `read_pdf_thetax` in
`Jeffrey_orbits.ipynb`).

## 6. Regeneration

Raw simulation data are not included in this dataset. The pickles are
regenerated from raw LAMMPS/Liggghts output with:

```bash
python main_orientations.py -c 0.4 -a 3.0 -v 0.1 -s 50 -np 8
# -> data/output_data_hertz/orientation_simple_shear_ap3.0_cof_0.4_I_0.1.pkl
```

## 7. License and citation

- Dataset: Creative Commons Attribution 4.0 (CC-BY-4.0).
- Code: GPL-3.0 — <https://github.com/JBil8/data_processing_orientations>.
- Please cite both; see `CITATION.cff` in the code repository.
