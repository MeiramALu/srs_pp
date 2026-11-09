/* falseshare.c - демонстрация ложного разделения (false sharing) в OpenMP.
 * Каждый поток увеличивает СВОЙ счётчик: (а) счётчики лежат рядом в одной строке кэша, (б) разнесены на 64 байта. */
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#define ITER 200000000L
int main(void) {
    int p = omp_get_max_threads();
    volatile long *packed = calloc(p, sizeof(long));
    volatile long *padded = calloc(p * 8, sizeof(long));
    double t0 = omp_get_wtime();
    #pragma omp parallel
    { int id = omp_get_thread_num(); for (long i = 0; i < ITER; i++) packed[id]++; }
    double ta = omp_get_wtime() - t0; t0 = omp_get_wtime();
    #pragma omp parallel
    { int id = omp_get_thread_num(); for (long i = 0; i < ITER; i++) padded[id * 8]++; }
    double tb = omp_get_wtime() - t0;
    printf("FALSESHARE threads=%d packed=%.3f padded=%.3f ratio=%.2f\n", p, ta, tb, ta / tb);
    return 0;
}
