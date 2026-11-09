/* solver_omp.c - реализация на OpenMP (общая память, fork-join).
 * gcc -O3 -g -fopenmp solver_omp.c -o solver_omp -lm ;  ./solver_omp N steps reps verify */
#include <stdio.h>
#include <omp.h>
#include "core.h"

static double *run(long N, long steps, double *time_out) {
    double *u = malloc((N + 2) * sizeof(double)), *v = malloc((N + 2) * sizeof(double));
    /* «первое касание» - параллельная инициализация, страницы размещаются рядом с потоками */
    #pragma omp parallel for schedule(static)
    for (long i = 0; i < N + 2; i++) {
        u[i] = (i == 0 || i == N + 1) ? 0.0 : init_val(i - 1, N);
        v[i] = 0.0;
    }
    double t0 = omp_get_wtime();
    #pragma omp parallel
    {
        int tid = omp_get_thread_num(), nt = omp_get_num_threads();
        double *a = u, *b = v;           /* у каждого потока свои указатели; меняются синхронно */
        for (long s = 0; s < steps; s++) {
            /* статическое разбиение work-sharing: поток tid обновляет свой блок */
            long lo = 1 + N * tid / nt, hi = 1 + N * (tid + 1) / nt;
            kernel(a, b, lo, hi);
            #pragma omp barrier
            double *t = a; a = b; b = t;
        }
    }
    *time_out = omp_get_wtime() - t0;
    double *res = (steps % 2) ? v : u, *other = (steps % 2) ? u : v;
    free(other);
    return res;
}

int main(int argc, char **argv) {
    long N = argc > 1 ? atol(argv[1]) : (1L << 24);
    long steps = argc > 2 ? atol(argv[2]) : 100;
    int reps = argc > 3 ? atoi(argv[3]) : 6;
    int verify = argc > 4 ? atoi(argv[4]) : 0;
    int p = omp_get_max_threads();
    if (verify) {
        double t; double *r = run(N, steps, &t), *ref = solve_serial(N, steps), d = 0;
        for (long i = 1; i <= N; i++) { double e = fabs(r[i] - ref[i]); if (e > d) d = e; }
        printf("VERIFY impl=omp N=%ld steps=%ld p=%d linf=%.3e\n", N, steps, p, d);
        return 0;
    }
    double *times = malloc(reps * sizeof(double));
    for (int k = 0; k < reps; k++) { double *r = run(N, steps, &times[k]); free(r); }
    printf("RESULT impl=omp N=%ld steps=%ld procs=1 threads=%d median=%.6f min=%.6f max=%.6f rss_mb=%.1f\n",
           N, steps, p, median_skip_first(times, reps), minv(times, reps), maxv(times, reps), maxrss_mb());
    return 0;
}
