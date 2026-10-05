import numpy as np
import argparse
import matplotlib.pyplot as plt
import os
import sys
import multiprocessing

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from ProcessorVtk import ProcessorVtk
from ProcessorDump import ProcessorDump
from CombinedProcessor import CombinedProcessor
from ReaderVtk import ReaderVtk
from ReaderDump import ReaderDump
from DataExporter import DataExporter
from ProcessorCsv import ProcessorCsv
from scipy.stats import binned_statistic
import scipy.optimize as spo


def parse_argument(value):
    try:
        # Try to convert to integer
        int_value = int(value)
        if float(value) == int_value:  # Ensure no decimals
            return int_value
    except ValueError:
        pass

    try:
        # Try to convert to float
        return float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid argument value: {value}")


def time_step_used(shear_rate, ap, factor, Young=5e6, rho=1000, nu=0.3, small_axis=1.0, shear_mod=1e6):
    """
    Compute the DEM stable time step using Hertz and Rayleigh contact time calculations.

    Parameters:
        shear_rate (float): Shear rate.
        ap (float): Aspect ratio (ratio of long to small axis for prolate shapes).
        factor (float): Factor to scale the computed time step.
        Young (float): Young's modulus of the material (default is 5e6).
        rho (float): Density of the material (default is 1000).
        nu (float): Poisson's ratio (default is 0.3).
        small_axis (float): Length of the smallest axis (default is 1.0).
        shear_mod (float): Shear modulus of the material (default is 1e6).

    Returns:
        float: The minimum time step for the simulation.
    """
    # Define the long axis and average diameter based on the particle shape
    long_axis = ap * small_axis
    if ap > 1:
        avg_diameter = (2 * small_axis + long_axis) / 3 * 2
    else:
        avg_diameter = (small_axis + 2 * long_axis) / 3 * 2

    # Calculate collision velocity
    v_collision = 2 * shear_rate * avg_diameter

    # Compute hertz and rayleigh time steps
    hertz_factor = 2.943 * (5 * np.sqrt(2) * np.pi *
                            rho * (1 - nu**2) / (4 * Young))**(2 / 5)
    min_dimen = min(small_axis, long_axis)
    dt_hertz = 2 * factor * hertz_factor * min_dimen / (v_collision)**(1 / 5)
    dt_rayleigh = 2 * factor * np.pi * min_dimen * \
        np.sqrt(rho / shear_mod) * (1 / (0.8766 + 0.1631 * nu))

    # Select the smaller of the Hertz and Rayleigh time steps
    dt = min(dt_hertz, dt_rayleigh)
    # print(f"Time step used: {dt}")
    return dt


def jeffrey_theoretical_velocity(shear_rate, ap, orientation):
    """
    Given the orientation(s) of the particle(s), compute the theoretical angular velocity.
    Handles both single vectors and arrays of vectors.
    """
    # Ensure orientation is a 2D array for consistent einsum behavior

    vorticity_tensor = np.array([[0, shear_rate/2, 0],
                                 [-shear_rate/2, 0, 0],
                                 [0, 0, 0]])
    strain_rate_tensor = np.array([[0, shear_rate/2, 0],
                                   [shear_rate/2, 0, 0],
                                   [0, 0, 0]])

    vorticity_tensor /= shear_rate
    strain_rate_tensor /= shear_rate

    beta = (ap**2 - 1) / (ap**2 + 1)

    vorticity_component = np.einsum('ij,nj->ni', vorticity_tensor, orientation)
    E_dot_u = np.einsum('ij,nj->ni', strain_rate_tensor, orientation)
    u_E_u = np.einsum('ni,ni->n', orientation, E_dot_u)
    straining_component = E_dot_u - u_E_u[:, np.newaxis] * orientation

    omega_jeffrey = beta * straining_component + vorticity_component
    return omega_jeffrey


def compute_jeffrey_screening(shear_rate, ap, orientations, omegas, theta_d):

    omegas /= shear_rate

    # angle with respect to flow direction in x-y plane
    theta_angles = np.arctan2(orientations[:, 1], orientations[:, 0])

    # reduce the angle to the range [-pi/2, pi/2]
    theta_angles = (theta_angles + np.pi/2) % np.pi - np.pi/2

    # bin thetas and the corresponding omegas at discrete values

    n_bins_theta = 15
    bins_theta = np.linspace(-np.pi/2, np.pi/2, n_bins_theta + 1)
    bin_centers = 0.5 * (bins_theta[:-1] + bins_theta[1:])
    bins_theta = np.linspace(-np.pi/2, np.pi/2, n_bins_theta + 1)

    # Extract the omega_z values
    omega_z = omegas[:, 2]

    # Use binned_statistic to calculate mean, std, and count in one pass
    #    We request three statistics for each bin.
    mean_stat, _, _ = binned_statistic(
        theta_angles, omega_z, statistic='mean', bins=bins_theta)
    std_stat, _, _ = binned_statistic(
        theta_angles, omega_z, statistic='std', bins=bins_theta)
    count_stat, _, _ = binned_statistic(
        theta_angles, omega_z, statistic='count', bins=bins_theta)

    # Calculate the standard error of the mean, handling bins with zero counts
    omega_std_per_bin = std_stat / np.sqrt(count_stat)

    # Clean up the results for empty bins (replace nan with 0)
    omega_per_bin = np.nan_to_num(mean_stat, nan=0.0)
    omega_std_per_bin = np.nan_to_num(omega_std_per_bin, nan=0.0)

    beta = (ap**2 - 1) / (ap**2 + 1)
    jeffrey_omega = -(1 - beta * np.cos(2 * (bin_centers))) / 2

    # compute the screening factor as the ratio the interpolate measured to jeffrey at the theta_d angle
    interpolated_measured = np.interp(theta_d, bin_centers, omega_per_bin)
    jeffrey_theta_d = -(1 - beta * np.cos(2 * theta_d)) / 2
    ratio = interpolated_measured / jeffrey_theta_d if jeffrey_theta_d != 0 else 0

    plt.figure(figsize=(4, 4))
    plt.plot(bin_centers, omega_per_bin, 'o-', label='Simulated', markersize=4)
    plt.plot(bin_centers, jeffrey_omega, '--', label='Jeffrey', color='red')
    plt.axvline(x=theta_d, color='green', linestyle=':',
                label='Director angle, ratio = %.2f' % ratio)
    plt.errorbar(bin_centers, omega_per_bin, yerr=omega_std_per_bin,
                 fmt='o', color='blue', alpha=0.5, label='Std Error', markersize=4)
    plt.xlabel(r'$\theta$ [rad]')
    plt.ylabel(r'$\omega_z / \dot{\gamma}$')
    plt.legend()
    plt.savefig('ap_' + str(ap) + 'mup_' + str(cof) + '_I_' +
                str(param) + '_jeffrey_comparison.png', bbox_inches='tight')
    plt.close()

    omega_jeffrey = jeffrey_theoretical_velocity(shear_rate, ap, orientations)
    dot_prod = np.einsum('ni, ni -> n', omega_jeffrey, omegas)
    # Covariance between theoretical and simulated angular velocities
    covariance = np.mean(dot_prod, axis=0)
    # Variance of the theoretical angular velocities
    variance_jeffrey = np.mean(
        np.einsum('ni, ni -> n', omega_jeffrey, omega_jeffrey), axis=0)
    if variance_jeffrey == 0:
        return 0
    # Screening factor for the Jeffrey model
    screening_factor = covariance / variance_jeffrey

    omega_z_measured = omegas[:, 2]
    omega_z_jeffrey = omega_jeffrey[:, 2]

    # The 'dot product' now becomes a simple element-wise product of the z-components
    product_z = omega_z_jeffrey * omega_z_measured

    # Covariance is the mean of this product
    covariance_z = np.mean(product_z)

    # Variance is the mean of the squared theoretical z-component
    variance_jeffrey_z = np.mean(omega_z_jeffrey**2)

    # Calculate the screening factor, with a check for division by zero
    if variance_jeffrey_z == 0:
        screening_factor_z = 0
    else:
        screening_factor_z = covariance_z / variance_jeffrey_z

    print(
        f"Screening factor: {screening_factor}, Screening factor z: {screening_factor_z}, Ratio at director angle: {ratio}")

    return screening_factor, bin_centers, omega_per_bin, omega_std_per_bin


def perform_block_analysis(orientations_flat, omegas_flat, n_particles, n_steps, shear_rate, ap, theta_d, n_blocks=1):
    """
    Performs block analysis on simulation data to find lambda and its error bar.

    Args:
        orientations_flat (np.ndarray): Flattened array of all orientations from all steps.
                                        Shape: (n_particles * n_steps, 3).
        omegas_flat (np.ndarray): Flattened array of all angular velocities from all steps.
                                  Shape: (n_particles * n_steps, 3).
        n_particles (int): The number of particles in the simulation.
        n_steps (int): The total number of time steps.
        shear_rate (float): The shear rate of the flow.
        ap (float): The aspect ratio of the particle.
        n_blocks (int): The number of blocks to divide the data into.

    Returns:
        tuple: A tuple containing (mean_lambda, error_bar).
    """
    # Reshape the flat data into a more useful format: (n_steps, n_particles, 3)
    orientations_t = orientations_flat.reshape(n_steps, n_particles, 3)
    omegas_t = omegas_flat.reshape(n_steps, n_particles, 3)

    block_size = n_steps // n_blocks
    lambdas_per_block = []

    # Loop over each block
    for i in range(n_blocks):
        start_step = i * block_size
        end_step = (i + 1) * block_size

        # Get the data for the current block
        orientations_block = orientations_t[start_step:end_step, :, :]
        omegas_block = omegas_t[start_step:end_step, :, :]

        # Flatten the block data to pass to the calculation function
        # The new shape is (block_size * n_particles, 3)
        orientations_block_flat = orientations_block.reshape(-1, 3)
        omegas_block_flat = omegas_block.reshape(-1, 3)

        # Calculate lambda for this block
        lambda_i, bins, omega_bins, std_omega_bins = compute_jeffrey_screening(
            shear_rate, ap, orientations_block_flat, omegas_block_flat, theta_d)
        lambdas_per_block.append(lambda_i)

    # Calculate the mean and standard error of the mean from the block values
    mean_lambda = np.mean(lambdas_per_block)
    # Use ddof=1 for sample standard deviation, as n_blocks is a small sample
    std_dev_of_lambdas = np.std(lambdas_per_block, ddof=1)
    error_bar = std_dev_of_lambdas / np.sqrt(n_blocks)

    ave_omega = np.mean(omegas_flat, axis=0) / shear_rate
    # print(f"Mean omega: {ave_omega}, Mean lambda: {mean_lambda}, Error bar: {error_bar}")

    return mean_lambda, error_bar, ave_omega, bins, omega_bins, std_omega_bins


def process_orientations(stacked_orientations):
    """
    Compute nematic parameters (S2, S4), tensors (Q, A4), and director.
    Masure how far from axisymmetric the distribution of orientations is.
    """
    N_strains = stacked_orientations.shape[0]

    order_tensor = np.einsum(
        'ij,ik->jk', stacked_orientations, stacked_orientations) / N_strains
    nematic_tensor = order_tensor - np.eye(3) / 3  # This is the Q-tensor

    eigenvalues, eigenvectors = np.linalg.eig(nematic_tensor)
    sorted_indices = np.argsort(eigenvalues)[::-1]  # Sort in descending order
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]

    director = eigenvectors[:, 0]  # Principal director (n)
    S2_scalar = 3.0 / 2.0 * eigenvalues[0]
    biaxiality = eigenvalues[1] - eigenvalues[2]  # Biaxiality parameter

    M4_tensor = np.einsum('ni,nj,nk,nl->ijkl', stacked_orientations,
                          stacked_orientations, stacked_orientations,
                          stacked_orientations) / N_strains

    # Define the isotropic fourth-order tensor (I_iso)
    delta = np.eye(3)
    I4_iso = (np.einsum('ij,kl->ijkl', delta, delta) +
              np.einsum('ik,jl->ijkl', delta, delta) +
              np.einsum('il,jk->ijkl', delta, delta)) / 15.0

    A4_tensor = M4_tensor - I4_iso
    cos_thetas = np.dot(stacked_orientations, director)

    S4_scalar = np.mean(P4(cos_thetas))

    # --- Original calculations for context ---
    # angle of the first eigenvector with respect to x-axis
    theta_d = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])
    angles_with_director = np.arccos(
        np.abs(np.dot(stacked_orientations, director)))  # Fold into [0, π/2]

    n_bins = 100
    f_data, edges = compute_polar_pdf(angles_with_director, n_bins=n_bins)
    bin_centers = 0.5 * (edges[:-1] + edges[1:])  # θ_i
    d_theta = edges[1] - edges[0]  # Δθ_i

    # Fit only U, holding S fixed
    def model(thetas, U): return fit_equilibrium_ODF(thetas, S2_scalar, U)

    initial_guess_U = 20
    popt, popv = spo.curve_fit(model, bin_centers, f_data, p0=[
                               initial_guess_U], method='lm', ftol=1e-8, maxfev=10000)
    U_fitted = popt[0]

    theta_fit = np.linspace(0, np.pi/2, 100)
    f_fit = fit_equilibrium_ODF(theta_fit, S2_scalar, U_fitted)

    # residuals = (f_data - model(bin_centers, U_fitted))**2 * np.sin(bin_centers) * d_theta
    # # chi_squared = np.sum(residuals * sin_theta_factor) / len(bin_centers)
    # rmse = np.sqrt(residuals)/(2 * np.pi)

    wsse = np.sum((f_data - model(bin_centers, U_fitted))**2
                  * np.sin(bin_centers) * d_theta)
    rmse_sphere = np.sqrt(wsse / 2)

    # print(f"Fitted U: {U_fitted:.3f}, RMSE: {rmse_sphere:.3f}, Nematic Order Parameter: {S2_scalar:.3f}, Biaxiality: {biaxiality:.3f}")

    plt.figure(figsize=(8, 5))
    plt.plot(bin_centers, f_data, 'o', markersize=4,
             label="Data (per solid angle)")
    plt.plot(theta_fit, f_fit, '--',
             label=f"Maier–Saupe fit (U={U_fitted:.3f})")
    plt.xlabel(r'$\theta$ [rad]')
    plt.ylabel(r'$f(\theta)$ (per unit solid angle)')
    plt.title('Orientation ODF and Maier–Saupe Fit')
    plt.grid(alpha=0.3)
    plt.ylim(0, 1.1 * np.max(f_data))
    plt.legend()
    # plt.tight_layout()
    plt.savefig('ap_' + str(ap) + '_cof_' + str(cof) + '_I_' +
                str(param) + '_orientation_ODF_fit.png', bbox_inches='tight')
    plt.close()

    angle_xy_plane = np.arctan2(
        stacked_orientations[:, 1], stacked_orientations[:, 0])
    angle_xy_plane = np.where(
        angle_xy_plane < 0, angle_xy_plane + np.pi, angle_xy_plane)
    angle_xy_plane = np.where(angle_xy_plane > np.pi/2,
                              angle_xy_plane - np.pi, angle_xy_plane)

    plt.figure(figsize=(6, 6))
    plt.hist(angle_xy_plane, bins=500, density=True, alpha=0.7, color='blue')
    plt.axvline(x=theta_d, color='red', linestyle='--', label='Director angle')
    plt.xlabel(r'$\phi$ [rad]')
    plt.ylabel('Probability Density')
    plt.title('Azimuthal Angle Distribution in the XY Plane')
    plt.grid(alpha=0.3)
    plt.savefig('ap_' + str(ap) + '_cof_' + str(cof) + '_I_' + str(param) +
                '_azimuthal_angle_distribution.png', bbox_inches='tight')
    plt.close()

    times, oacf, D_r, Pe, tau_r, A_infty = measure_rotational_diffusion(
        stacked_orientations, 2000, shear_rate, n_starting_points=40, max_lag=None)

    # build a dictionary with the results
    results = {}
    results['bin_centers'] = bin_centers
    results['f_data'] = f_data
    results['U_fitted'] = U_fitted
    results['director'] = director
    results['S2_scalar'] = S2_scalar
    results['S4_scalar'] = S4_scalar
    results['biaxiality'] = biaxiality
    results['theta_d'] = theta_d
    results['eigenvalues'] = eigenvalues
    results['eigenvectors'] = eigenvectors
    results['rmse_fit'] = rmse_sphere
    results['times'] = times
    results['oacf'] = oacf
    results['D_r'] = D_r
    results['Pe'] = Pe
    results['tau_r'] = tau_r
    results['A_infty'] = A_infty
    results['shear_rate'] = shear_rate
    results['S4'] = A4_tensor
    results['nematic_tensor'] = nematic_tensor
    return results


def S2_to_gamma(results, shear_rate, n_particles):

    orientations = np.concatenate([result['directors'] for result in results])
    n_frames = orientations.shape[0] // n_particles
    orientations = orientations.reshape(n_frames, n_particles, 3)

    Identity = np.eye(3)
    order_tensor = np.einsum(
        'ijk,ijl->ikl', orientations, orientations)/n_particles
    order_tensor -= Identity[np.newaxis, :, ]/3

    # angle with the flow direction from director
    eigenvalues, eigenvectors = np.linalg.eigh(order_tensor)

    # The largest eigenvalue is the last one in each frame's set.
    largest_eigenvalues = eigenvalues[:, -1]
    order_parameters = 3/2 * largest_eigenvalues  # Nematic order parameter S2

    biaxiality = eigenvalues[:, 1] - eigenvalues[:, 0]  # Biaxiality parameter

    # The director n is the eigenvector corresponding to the largest eigenvalue.
    directors = eigenvectors[:, :, -1]  # Shape: (n_frames, 3)
    flip_mask = directors[:, 0] < 0
    # Use the mask to flip the sign of the entire director vector for those frames.
    directors[flip_mask] = -directors[flip_mask]
    # Extract the x and y components of the director for each frame
    nx = directors[:, 0]
    ny = directors[:, 1]

    # Calculate the angle in the xy-plane using arctan2 for quadrant correctness.
    # The result is in radians, in the range [-pi, pi].
    angles_rad = np.arctan2(ny, nx)

    gammas = np.linspace(0, 30, n_frames)

    return order_parameters, gammas, angles_rad, biaxiality


def measure_rotational_diffusion(stacked_orientations, n_particles, shear_rate, n_starting_points=10, max_lag=None):
    """
    Measure rotational diffusion coefficient D_r via autocorrelation of P2(u · u')

    Parameters:
    - stacked_orientations: (n_frames * n_particles, 3) array of unit vectors
    - n_particles: Number of particles
    - shear_rate: known shear rate (used to compute time step)
    - n_starting_points: number of evenly spaced starting time points to average over
    - max_lag: maximum number of time lags (optional, default: all possible)

    Returns:
    - times: array of times corresponding to lags
    - C: autocorrelation array (averaged over particles and starting points)
    """
    delta_gamma = 1 / 100  # time step in shear units
    delta_t = delta_gamma / shear_rate

    n_total = stacked_orientations.shape[0]
    n_frames = n_total // n_particles

    # Reshape to (n_frames, n_particles, 3)
    orientations = stacked_orientations.reshape(n_frames, n_particles, 3)

    if max_lag is None:
        max_lag = n_frames // 2

    # Choose starting indices evenly spaced
    start_indices = np.linspace(
        0, n_frames - max_lag - 1, n_starting_points, dtype=int)

    oacf = np.zeros(max_lag)
    for start in start_indices:
        u0 = orientations[start]  # shape (n_particles, 3)
        for lag in range(max_lag):
            u_t = orientations[start + lag]  # shape (n_particles, 3)
            # dot product u(0) · u(t) for all particles
            dot = np.einsum('ij,ij->i', u0, u_t)
            oacf[lag] += (dot**2).mean()

    oacf /= len(start_indices)

    times = np.arange(max_lag) * delta_t

    def long_time_decay(t, A_infty, tau_r):
        """
        Model for the autocorrelation function: A_infty + oacf * exp(-t/tau_r)
        """
        return A_infty + (1 - A_infty) * np.exp(-t / tau_r)

    # perform the fit to exrtract A_infty and tau_r
    initial_guess = [0, 1]  # Initial guess for A_infty and tau_r
    try:
        popt, _ = spo.curve_fit(long_time_decay, times,
                                oacf, p0=initial_guess, maxfev=10000)
        A_infty, tau_r = popt

    except RuntimeError as e:
        print(f"Fit failed: {e}")
        A_infty, tau_r = 0, 1  # Default values if fit fails

    D_r = (1 - A_infty) / (4 * tau_r)  # Rotational diffusion coefficient
    Pe = shear_rate / D_r  # Peclet number

    return times, oacf, D_r, Pe, tau_r, A_infty


def P2(x):
    """
    Calculates the second Legendre polynomial
    """
    return (3 * x**2 - 1) / 2


def P4(x):
    """
    Calculates the fourth Legendre polynomial
    """
    return (35 * x**4 - 30 * x**2 + 3) / 8


def fit_equilibrium_ODF(measured_thetas, S, U):
    """
    Maier-Saupe equilibrium distribution per unit solid angle,
    using the second Legendre Polynomial P₂(cosθ).
    Accounts for head-tail symmetry (θ ∈ [0, π/2]).
    Normalization is computed over [0, π/2] and multiplied by 2 to account for symmetry.
    """
    # Calculate the cosine of the angles, which is the argument for P₂
    cos_thetas = np.cos(measured_thetas)

    # The argument of the exponential is now based on the Legendre polynomial
    legendre_term = P2(cos_thetas)

    # The numerator now uses the physically standard Maier-Saupe potential
    # The potential is proportional to U * S * P₂(cosθ)
    numerator = np.exp(S * U * legendre_term)

    # The normalization procedure remains identical, as it correctly integrates
    # the un-normalized probability over the solid angle.
    integrand = numerator * np.sin(measured_thetas)
    denominator = 4 * np.pi * np.trapezoid(integrand, x=measured_thetas)

    return numerator / denominator


def compute_polar_pdf(theta_array, n_bins=50):
    """
    Compute the normalized PDF of polar angles theta_array over [0, pi],
    accounting for spherical geometry (sin(theta) weighting).
    """
    # Bin edges and centers
    bins = np.linspace(0, np.pi/2, n_bins + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    delta_theta = bins[1] - bins[0]

    # Histogram of theta values
    counts, edges = np.histogram(theta_array, bins=bins)

    # Weight for spherical coordinates (sin(theta))
    sin_theta = np.sin(centers)

    # Normalize to get PDF f(theta), such that:
    # 2π ∫ f(θ) sin(θ) dθ = 1
    pdf = counts / (4 * np.pi * sin_theta * delta_theta * len(theta_array))

    return pdf, edges


def process_results(results):
    """Extract the orientation distributions from the per-step results."""

    directors = np.concatenate([result['directors'] for result in results])
    omegas = np.concatenate([result['omegas'] for result in results])

    results = process_orientations(directors)

    screening_jeffrey, error_screening, ave_omega, bins, omega_bins, std_omega_bins = perform_block_analysis(
        directors, omegas, 2000, n_sim, shear_rate, ap, results['theta_d'])

    results['screening_jeffrey'] = screening_jeffrey
    results['error_screening'] = error_screening
    results['ave_omega'] = ave_omega
    results['theta_bins'] = bins
    results['omega_bins'] = omega_bins
    results['std_omega_bins'] = std_omega_bins

    return results


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Process granular simulation.')
    parser.add_argument('-c', '--cof', type=float,
                        help='coefficient of friction particles-particles')
    parser.add_argument('-a', '--ap', type=float, help='aspect ratio')
    parser.add_argument('-v', '--value', type=float,
                        help='packing fraction or Inertial number depensing on the type of simulation')
    parser.add_argument('-p', '--postprocess', action='store_false',
                        help='whether to postprocess the data or simply import the pkl file, default is True', default=True)
    parser.add_argument('-cw', '--cof_wall', action='store_false',
                        help='coefficient of friction particles-walls')
    parser.add_argument('-s', '--pressure',
                        type=parse_argument, help='pressure')
    parser.add_argument('-np', '--num_processes', type=int,
                        help='number of processes to use in parallel', default=8)
    parser.add_argument('-d', '--input_dir', type=str,
                        help='path to the directory containing the raw simulation data '
                             '(directories alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/)')
    args = parser.parse_args()

    # parsing command line arguments
    cof = args.cof
    ap = args.ap
    param = args.value
    full_postprocess = args.postprocess
    pressure = args.pressure
    num_processes = args.num_processes
    global_path = args.input_dir

    if full_postprocess == True:

        # alternative cluster paths:
        plt.ioff()
        # initialize the vtk reader
        data_read = ReaderVtk(cof, ap, I=param, pressure=pressure)
        data_read.read_data(global_path, 'simple_shear_', box=True)
        data_read.no_wall_atoms()
        data_read.get_initial_velocities_and_orientations()
        df_csv, shear_rate = data_read.read_csv_file()
        dt_hertz = time_step_used(shear_rate, ap, 1.5*0.08)

        # intialize the dump reader
        data_dump = ReaderDump(cof, ap, I=param, pressure=pressure)
        data_dump.read_data(global_path, 'simple_shear_contact_data_')
        to_process_vtk = ProcessorVtk(data_read)
        to_process_dump = ProcessorDump(
            data_dump, data_read.n_wall_atoms, data_read.n_central_atoms)
        combined_processor = CombinedProcessor(
            to_process_vtk, to_process_dump, data_read.file_list_box, shear_rate, dt_hertz)

        if param >= 0.01:
            shear_one_index = 2000
        else:
            shear_one_index = 400
        print("Shear one index: ", shear_one_index)
        n_sim = combined_processor.n_sim-shear_one_index
        with multiprocessing.Pool(num_processes) as pool:
            results = pool.map(combined_processor.process_single_step,
                               [step for step in range(shear_one_index, combined_processor.n_sim)])

        # averages, hist_weigh_avg, pdfs, distributions = process_results(results, num_bins_global, num_bins_local)
        orientation_dict = process_results(results)

        # Compute nematic parameter and show it is steady state
        with multiprocessing.Pool(num_processes) as pool:
            results_time = pool.map(combined_processor.process_single_step,
                                    [step for step in range(combined_processor.n_sim)])

        S2_over_time, strains, angle_over_time, biaxility_over_time = S2_to_gamma(
            results_time, shear_rate, 2000)

        orientation_dict['S2_over_time'] = S2_over_time
        orientation_dict['strains'] = strains
        orientation_dict['angle_over_time'] = angle_over_time
        orientation_dict['biaxility_over_time'] = biaxility_over_time

        csvProcessor = ProcessorCsv(df_csv)
        csvProcessor.exclude_initial_strain_cycle(param)
        avgCsv = csvProcessor.get_averages(shear_rate)
        fluctuationsCsv = csvProcessor.get_fluctuations(avgCsv)

        # export the data with pickle
        averages = {**avgCsv,   **orientation_dict, **fluctuationsCsv}

        exporter = DataExporter(ap, cof, I=param)
        exporter.export_orientation_data(averages)
        # exporter.export_with_pickle(averages)

    else:
        # import the data with pickle
        importer = DataExporter(ap, cof, I=param)
        averages = importer.import_with_pickle()
        print("Loaded keys:", list(averages.keys()))
