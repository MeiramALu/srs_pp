#!/bin/bash
# Полный набор измерений SIW 2. Запускать в WSL/Linux после build.sh.  Результат: results/*.txt
# Размещение задаётся явно: каждому MPI-процессу выделяется непрерывный набор из 16/R аппаратных потоков,
# потоки OpenMP внутри набора раскладываются OMP_PROC_BIND=spread, OMP_PLACES=threads.
cd "$(dirname "$0")/.."
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export OMP_PLACES=threads OMP_PROC_BIND=spread
mkdir -p results
N=${N:-16777216}; S=${S:-100}; REPS=${REPS:-6}
MPIRUN() { local R=$1; shift; mpirun -n $R --use-hwthread-cpus --map-by ppr:$R:node:PE=$((16/R)) --bind-to hwthread "$@"; }

echo "# $(date) N=$N steps=$S reps=$REPS" > results/scaling.txt
for p in 1 2 4 8 16; do
  OMP_NUM_THREADS=$p ./bin/solver_omp $N $S $REPS >> results/scaling.txt
  OMP_NUM_THREADS=1 MPIRUN $p ./bin/solver_mpi $N $S $REPS >> results/scaling.txt
  if [ $p -eq 1 ]; then R=1; T=1; else R=2; T=$((p/2)); fi
  OMP_NUM_THREADS=$T MPIRUN $R ./bin/solver_hyb $N $S $REPS >> results/scaling.txt
done

echo "# hybrid divisions, total 16 hardware threads" > results/hybrid.txt
for cfg in "16 1" "8 2" "4 4" "2 8" "1 16"; do
  set -- $cfg
  OMP_NUM_THREADS=$2 MPIRUN $1 ./bin/solver_hyb $N $S $REPS >> results/hybrid.txt
done

echo "# memory: 16 MPI processes vs 1 process x 16 threads vs hybrid 2x8" > results/memory.txt
for n in 65536 1048576 16777216 67108864; do
  OMP_NUM_THREADS=16 ./bin/solver_omp $n 4 3 >> results/memory.txt
  OMP_NUM_THREADS=1 MPIRUN 16 ./bin/solver_mpi $n 4 3 >> results/memory.txt
  OMP_NUM_THREADS=8 MPIRUN 2 ./bin/solver_hyb $n 4 3 >> results/memory.txt
done

echo "# pingpong (2 ranks on different cores, shared-memory transport)" > results/pingpong.txt
mpirun -n 2 --use-hwthread-cpus --map-by ppr:2:node:PE=8 --bind-to hwthread ./bin/pingpong >> results/pingpong.txt

echo "# false sharing" > results/falseshare.txt
for t in 2 4 8; do OMP_NUM_THREADS=$t ./bin/falseshare >> results/falseshare.txt; done

echo "# system" > results/system.txt
lscpu | grep -E "Model name|^CPU\(s\)|Thread|Core|Socket|L1d|L2|L3|NUMA node\(s\)" >> results/system.txt
free -m | head -2 >> results/system.txt
mpirun --version | head -1 >> results/system.txt
gcc --version | head -1 >> results/system.txt
echo done
