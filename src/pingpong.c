/* pingpong.c - измерение времени пересылки T(M) между двумя рангами для подгонки Tcomm = ts + M/B.
 * mpirun -n 2 ./pingpong  -> строки "PP bytes=.. time_us=.." (одностороннее время, медиана) */
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
static int cmpd(const void *a, const void *b) { double x = *(double *)a, y = *(double *)b; return (x > y) - (x < y); }
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank; MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    long maxb = 1L << 26; char *buf = calloc(maxb, 1);
    for (long m = 1; m <= maxb; m *= 2) {
        int reps = m <= 4096 ? 4001 : (m <= (1 << 20) ? 501 : 41);
        double *t = malloc(reps * sizeof(double));
        for (int k = 0; k < reps; k++) {
            MPI_Barrier(MPI_COMM_WORLD);
            double t0 = MPI_Wtime();
            if (rank == 0) { MPI_Send(buf, (int)m, MPI_BYTE, 1, 0, MPI_COMM_WORLD); MPI_Recv(buf, (int)m, MPI_BYTE, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE); }
            else           { MPI_Recv(buf, (int)m, MPI_BYTE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE); MPI_Send(buf, (int)m, MPI_BYTE, 0, 0, MPI_COMM_WORLD); }
            t[k] = (MPI_Wtime() - t0) / 2.0;
        }
        qsort(t + 1, reps - 1, sizeof(double), cmpd);   /* первый прогон отбрасываем */
        if (rank == 0) printf("PP bytes=%ld time_us=%.4f\n", m, t[1 + (reps - 1) / 2] * 1e6);
        free(t);
    }
    MPI_Finalize(); return 0;
}
