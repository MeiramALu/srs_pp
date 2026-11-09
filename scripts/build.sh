#!/bin/bash
# Сборка всех программ (запускать в WSL/Linux). Результат - в ./bin
set -e
cd "$(dirname "$0")/../src"; mkdir -p ../bin
gcc   -O3 -g -fopenmp solver_omp.c -o ../bin/solver_omp -lm
mpicc -O3 -g solver_mpi.c -o ../bin/solver_mpi -lm
mpicc -O3 -g -fopenmp -DHYBRID solver_mpi.c -o ../bin/solver_hyb -lm
mpicc -O3 -g pingpong.c -o ../bin/pingpong
gcc   -O1 -g -fopenmp falseshare.c -o ../bin/falseshare
echo build ok
