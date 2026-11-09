/* solver_mpi.c - реализация на MPI (раздельная память, SPMD), разбиение области на полосы.
 * mpicc -O3 -g solver_mpi.c -o solver_mpi -lm ;  mpirun -n 8 ./solver_mpi N steps reps verify
 * Если скомпилировано с -DHYBRID -fopenmp - гибрид MPI+OpenMP (solver_hyb). */
#include <stdio.h>
#include <mpi.h>
#ifdef HYBRID
#include <omp.h>
#endif
#include "core.h"

static void halo(double *a, long n, int rank, int size, MPI_Comm c) {
    int left = rank > 0 ? rank - 1 : MPI_PROC_NULL, right = rank < size - 1 ? rank + 1 : MPI_PROC_NULL;
    MPI_Sendrecv(&a[1], 1, MPI_DOUBLE, left, 0, &a[n + 1], 1, MPI_DOUBLE, right, 0, c, MPI_STATUS_IGNORE);
    MPI_Sendrecv(&a[n], 1, MPI_DOUBLE, right, 1, &a[0], 1, MPI_DOUBLE, left, 1, c, MPI_STATUS_IGNORE);
}

static double *run(long n, long off, long N, long steps, int rank, int size, double *time_out) {
    double *u = malloc((n + 2) * sizeof(double)), *v = malloc((n + 2) * sizeof(double));
#ifdef HYBRID
    #pragma omp parallel for schedule(static)
#endif
    for (long i = 0; i < n + 2; i++) {
        long g = off + i - 1;                              /* глобальный индекс */
        u[i] = (g < 0 || g >= N) ? 0.0 : init_val(g, N);
        v[i] = 0.0;
    }
    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
#ifdef HYBRID
    #pragma omp parallel
    {
        int tid = omp_get_thread_num(), nt = omp_get_num_threads();
        double *a = u, *b = v;
        for (long s = 0; s < steps; s++) {
            #pragma omp master
            halo(a, n, rank, size, MPI_COMM_WORLD);        /* MPI_THREAD_FUNNELED: вызывает только master */
            #pragma omp barrier
            { long lo = 1 + n * tid / nt, hi = 1 + n * (tid + 1) / nt; kernel(a, b, lo, hi); }
            #pragma omp barrier
            double *t = a; a = b; b = t;
        }
    }
#else
    {
        double *a = u, *b = v;
        for (long s = 0; s < steps; s++) {
            halo(a, n, rank, size, MPI_COMM_WORLD);
            kernel(a, b, 1, n + 1);
            double *t = a; a = b; b = t;
        }
    }
#endif
    MPI_Barrier(MPI_COMM_WORLD);
    double dt = MPI_Wtime() - t0, mx;
    MPI_Allreduce(&dt, &mx, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
    *time_out = mx;
    double *res = (steps % 2) ? v : u, *other = (steps % 2) ? u : v;
    free(other);
    return res;
}

int main(int argc, char **argv) {
    int rank, size, provided = 0;
#ifdef HYBRID
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    const char *impl = "hyb"; int thr = omp_get_max_threads();
#else
    MPI_Init(&argc, &argv);
    const char *impl = "mpi"; int thr = 1;
#endif
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size);
    long N = argc > 1 ? atol(argv[1]) : (1L << 24);
    long steps = argc > 2 ? atol(argv[2]) : 100;
    int reps = argc > 3 ? atoi(argv[3]) : 6;
    int verify = argc > 4 ? atoi(argv[4]) : 0;
    long base = N / size, rem = N % size;
    long n = base + (rank < rem ? 1 : 0), off = rank * base + (rank < rem ? rank : rem);

    if (verify) {
        double t; double *r = run(n, off, N, steps, rank, size, &t);
        int *cnt = NULL, *dsp = NULL; double *all = NULL;
        if (rank == 0) { cnt = malloc(size * sizeof(int)); dsp = malloc(size * sizeof(int)); all = malloc(N * sizeof(double)); }
        int ni = (int)n, oi = (int)off;
        MPI_Gather(&ni, 1, MPI_INT, cnt, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Gather(&oi, 1, MPI_INT, dsp, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Gatherv(&r[1], ni, MPI_DOUBLE, all, cnt, dsp, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        if (rank == 0) {
            double *ref = solve_serial(N, steps), d = 0;
            for (long i = 0; i < N; i++) { double e = fabs(all[i] - ref[i + 1]); if (e > d) d = e; }
            printf("VERIFY impl=%s N=%ld steps=%ld procs=%d threads=%d linf=%.3e\n", impl, N, steps, size, thr, d);
        }
        MPI_Finalize(); return 0;
    }
    double *times = malloc(reps * sizeof(double));
    for (int k = 0; k < reps; k++) { double *r = run(n, off, N, steps, rank, size, &times[k]); free(r); }
    double rss = maxrss_mb(), tot;
    MPI_Reduce(&rss, &tot, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("RESULT impl=%s N=%ld steps=%ld procs=%d threads=%d median=%.6f min=%.6f max=%.6f rss_mb=%.1f\n",
               impl, N, steps, size, thr, median_skip_first(times, reps), minv(times, reps), maxv(times, reps), tot);
    MPI_Finalize();
    return 0;
}
