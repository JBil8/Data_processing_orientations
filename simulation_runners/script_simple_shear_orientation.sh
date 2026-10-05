#!/bin/bash

# --- Paths to edit per machine -------------------------------------------
# Full path to the (patched) LIGGGHTS executable
executable="/home/jacopo/opt/LIGGGHTS-PUBLIC/src/liggghts"
# Input script (expected in this directory)
input_script="in.simple_shear_le_orientation"
# Root directory where the run directories alpha_{ap}_cof_{cof}_pressure_{s}_I_{I}/ are created
run_root="/scratch/bilotto/simulations_simple_shear_orientation_N4000_long_box"
# --------------------------------------------------------------------------

# Directory containing this script and the input scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define parameter arrays
radius=1
density=1000
YoungMod="5.0e6"
# aspectRatios=(1.2 1.5 1.8 2.0 2.5 3.0 3.5 4.0 4.5 5.0 5.5 6.0 7.0 8.0)
inertialNumbers=(0.1)
cofs=(0.0 0.001 0.01 0.1 0.4 1.0 10.0 100.0)
# Define the maximum number of parallel tasks
ntasks=1
pressure_target=50

echo "Start of the loop"

for COF in "${cofs[@]}"; do
    # Loop through the values of aspectRatio
    for aspectRatio in "${aspectRatios[@]}"; do

        # Loop through the values of inertialNumbers
        for I in "${inertialNumbers[@]}"; do    
            
            # The run directory matches what the post-processing pipeline expects
            target_dir="${run_root}/alpha_${aspectRatio}_cof_${COF}_pressure_${pressure_target}_I_${I}"
            
            mkdir -p "$target_dir"
            
            job_script="$target_dir/job_${COF}_${aspectRatio}.sh"
            
            echo "#!/bin/bash" > "$job_script"
            echo "#SBATCH --job-name=_alpha_${aspectRatio}_s_${ntasks}_cof_${COF}" >> "$job_script"
            echo "#SBATCH --output=output_%j.txt" >> "$job_script"
            echo "#SBATCH --error=error_%j.txt" >> "$job_script"
            echo "#SBATCH --ntasks=${ntasks}" >> "$job_script"
            echo "#SBATCH --cpus-per-task=1" >> "$job_script"
            echo "#SBATCH --mem=6G" >> "$job_script"
            echo "#SBATCH --time=3-00:00:00" >> "$job_script"
            echo "#SBATCH --mail-type=BEGIN,END,FAIL" >> "$job_script"
            echo "#SBATCH --mail-user=jacopo.bilotto@epfl.ch" >> "$job_script"
            
            # Navigate to the correct folder inside the Slurm allocation
            echo "cd $target_dir" >> "$job_script"
            
            # Run LIGGGHTS from the run directory, passing the paths of the input scripts
            echo "srun $executable -v density $density -v aspectRatio $aspectRatio -v COF $COF -v Radius $radius -v I $I -v YoungMod $YoungMod -v pressure_target $pressure_target -v insertion_script ${SCRIPT_DIR}/in.insertion -in ${SCRIPT_DIR}/${input_script}" >> "$job_script"
            
            chmod +x "$job_script"
            sbatch "$job_script"
        done
    done
done

echo "All jobs submitted to Slurm."
