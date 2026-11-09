#!/bin/bash
# Второй набор: задача целиком помещается в кэш (N=2^18, 4 МБ), 8000 шагов - упор в синхронизацию, а не в память.
cd "$(dirname "$0")/.."
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export OMP_PLACES=threads OMP_PROC_BIND=spread
N=262144; S=8000; REPS=11
MPIRUN() { local R=$1; shift; mpirun -n $R --use-hwthread-cpus --map-by ppr:$R:node:PE=$((16/R)) --bind-to hwthread "$@"; }
echo "# cache-resident: N=$N steps=$S reps=$REPS" > results/scaling_cache.txt
for p in 1 2 4 8 16; do
  OMP_NUM_THREADS=$p ./bin/solver_omp $N $S $REPS >> results/scaling_cache.txt
  OMP_NUM_THREADS=1 MPIRUN $p ./bin/solver_mpi $N $S $REPS >> results/scaling_cache.txt
  if [ $p -eq 1 ]; then R=1; T=1; else R=2; T=$((p/2)); fi
  OMP_NUM_THREADS=$T MPIRUN $R ./bin/solver_hyb $N $S $REPS >> results/scaling_cache.txt
done
echo "# hybrid divisions, cache-resident" > results/hybrid_cache.txt
for cfg in "16 1" "8 2" "4 4" "2 8" "1 16"; do
  set -- $cfg
  OMP_NUM_THREADS=$2 MPIRUN $1 ./bin/solver_hyb $N $S $REPS >> results/hybrid_cache.txt
done
echo done
