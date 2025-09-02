#!/bin/bash

# # Define the parameters
# aspectRatios=(1.0 1.2 1.5 1.8 2.0 2.5 3.0)
cofs=(0.0 0.001 0.01 0.1 0.4 1.0 10.0)
# # aspectRatios=(0.33 0.40 0.50 0.56 0.67 0.83)
# # aspectRatios=(3.0)
# # cofs=(0.0)
# Is=(0.1 0.046 0.022 0.01 0.0046 0.0022 0.001)

# aspectRatios=(0.33 0.4 0.5 0.56 0.67 0.83 1.0)
aspectRatios=(6.0 8.0 10.0)
aspectRatios=(1.2 1.5 1.8 2.0 2.5 3.0 3.5 4.0 4.5 5.0 5.5 6.0 7.0 8.0 9.0)

# inertialNumbers=(0.001)
# cofs=(0.0)
Is=(0.1)
s=50
# Define the maximum number of parallel tasks
max_parallel_tasks=10
cpus=8

echo "Start of the loop"

# Loop through the values of -var flag for COF
for cof in "${cofs[@]}"
do
    # Loop through the values of -var flag for ap
    for ap in "${aspectRatios[@]}"
    do
        # Determine value of s based on ap
        if (( $(echo "$ap < 1" | bc -l) )); then
            s=$(echo "scale=1; 50 * $ap" | bc -l)
        fi

        # Optional: Print to check
        echo "cof=$cof, ap=$ap, s=$s"
        # Loop through the values of -var flag for phi
        for I in "${Is[@]}"
        do
            # Submit the job directly to sbatch
            sbatch <<EOL
#!/bin/bash
#SBATCH -n 1 #Request 1 task (core)
#SBATCH --ntasks=1                      # Number of tasks (processes)
#SBATCH --cpus-per-task=$cpus              # Number of CPU cores per task
#SBATCH -t 0-10:00 #Request runtime of 1 hour
##SBATCH -o output_post_%j.txt #redirect output to output_post_JOBID.txt
##SBATCH -e error_post_%j.txt #redirect errors to error_post_JOBID.txt
python main_orientations.py -c $cof -a $ap -v $I -s $s -np $cpus
EOL

            # Limit the number of parallel tasks
            running_tasks=$(jobs -p | wc -l)
            while [ $running_tasks -ge $max_parallel_tasks ]; do
                sleep 1
                running_tasks=$(jobs -p | wc -l)
            done
        done
    done
done

# Wait for all background jobs to finish
wait

echo "All post-processing jobs submitted to Slurm."
