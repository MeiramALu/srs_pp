#!/bin/bash
# Проверка корректности: L_inf-норма разности с последовательной версией (N не кратно числу процессов намеренно)
cd "$(dirname "$0")/.."
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 OMPI_MCA_rmaps_base_oversubscribe=1
N=1000003; S=200
for p in 1 2 4 8 16; do
  OMP_NUM_THREADS=$p ./bin/solver_omp $N $S 6 1
done
for p in 1 2 4 8 16; do
  mpirun -n $p --use-hwthread-cpus ./bin/solver_mpi $N $S 6 1
done
for cfg in "16 1" "8 2" "4 4" "2 8" "1 16"; do
  set -- $cfg
  OMP_NUM_THREADS=$2 mpirun -n $1 --use-hwthread-cpus ./bin/solver_hyb $N $S 6 1
done
