/* core.h - общее численное ядро для всех трёх реализаций (SIW 2).
 * Уравнение теплопроводности u_t = a*u_xx, явная схема FTCS, r = a*dt/dx^2 = 0.25 (устойчиво при r<=0.5).
 * Массив с «призрачными» ячейками: u[0] и u[N+1] - границы Дирихле (=0), u[1..N] - внутренние узлы. */
#ifndef CORE_H
#define CORE_H
#include <math.h>
#include <stdlib.h>
#include <sys/resource.h>

#define R_COEF 0.25

/* начальное условие для глобального узла i (0..N-1) */
static inline double init_val(long i, long N) {
    double x = (double)(i + 1) / (double)(N + 1);
    return sin(M_PI * x) + 0.5 * sin(3.0 * M_PI * x);
}

/* ОДИН узел схемы - одно и то же выражение во всех реализациях */
static inline double heat_point(const double *u, long i) {
    return u[i] + R_COEF * (u[i - 1] - 2.0 * u[i] + u[i + 1]);
}

/* Ядро: обновление диапазона [lo,hi) - одна и та же функция во всех реализациях (restrict даёт компилятору право векторизовать) */
static inline void kernel(const double *restrict a, double *restrict b, long lo, long hi) {
    for (long i = lo; i < hi; i++) b[i] = heat_point(a, i);
}

/* последовательный эталон: возвращает массив длины N+2 (результат после steps шагов) */
static double *solve_serial(long N, long steps) {
    double *u = calloc(N + 2, sizeof(double)), *v = calloc(N + 2, sizeof(double));
    for (long i = 0; i < N; i++) u[i + 1] = init_val(i, N);
    for (long s = 0; s < steps; s++) {
        kernel(u, v, 1, N + 1);
        double *t = u; u = v; v = t;
    }
    free(v);
    return u;
}

static int cmpd(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}
/* медиана после отбрасывания первого прогона */
static double median_skip_first(double *t, int reps) {
    int n = reps - 1;
    double *c = malloc(n * sizeof(double));
    for (int i = 1; i < reps; i++) c[i - 1] = t[i];
    qsort(c, n, sizeof(double), cmpd);
    double m = (n % 2) ? c[n / 2] : 0.5 * (c[n / 2 - 1] + c[n / 2]);
    free(c);
    return m;
}
static double minv(double *t, int n) { double m = t[1]; for (int i = 1; i < n; i++) if (t[i] < m) m = t[i]; return m; }
static double maxv(double *t, int n) { double m = t[1]; for (int i = 1; i < n; i++) if (t[i] > m) m = t[i]; return m; }
static double maxrss_mb(void) { struct rusage ru; getrusage(RUSAGE_SELF, &ru); return ru.ru_maxrss / 1024.0; }
#endif
