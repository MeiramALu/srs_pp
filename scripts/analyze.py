"""Обработка результатов измерений: таблицы (results/summary.json) и графики (figures/*.png).
Запуск: .venv\\Scripts\\python scripts\\analyze.py"""
import json, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES, FIG = ROOT / "results", ROOT / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": .3, "figure.dpi": 150})
COL = {"omp": "#1f77b4", "mpi": "#d62728", "hyb": "#2ca02c"}
NAME = {"omp": "OpenMP", "mpi": "MPI", "hyb": "MPI+OpenMP"}


def parse(fn, tag):
    out = []
    for line in (RES / fn).read_text(encoding="utf8").splitlines():
        if line.startswith(tag):
            out.append({k: (float(v) if re.fullmatch(r"-?[\d.]+(e[-+]?\d+)?", v) else v)
                        for k, v in (kv.split("=") for kv in line.split()[1:])})
    return out


S = {}
# ---------- масштабирование ----------
sc = parse("scaling.txt", "RESULT")
tot = lambda r: int(r["procs"] * r["threads"])
t1 = {}
for r in sc:
    if tot(r) == 1:
        t1[r["impl"]] = r["median"]
# T(1) для всех реализаций сравниваем с собственной единичной конфигурацией (по формуле (2));
# дополнительно считаем ускорение относительно лучшего T(1) (OpenMP при 1 потоке ~ последовательная программа)
tbase = min(t1.values())
rows = []
for r in sc:
    p = tot(r)
    rows.append(dict(impl=r["impl"], p=p, procs=int(r["procs"]), threads=int(r["threads"]), T=r["median"],
                     Tmin=r["min"], Tmax=r["max"], S=t1[r["impl"]] / r["median"],
                     E=t1[r["impl"]] / r["median"] / p, S_abs=tbase / r["median"]))
S["scaling"] = rows
S["N"] = int(sc[0]["N"]); S["steps"] = int(sc[0]["steps"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
ps = [1, 2, 4, 8, 16]
for impl in ("omp", "mpi", "hyb"):
    rr = sorted([x for x in rows if x["impl"] == impl], key=lambda x: x["p"])
    ax[0].loglog([x["p"] for x in rr], [x["S"] for x in rr], "o-", color=COL[impl], label=NAME[impl])
    ax[1].loglog([x["p"] for x in rr], [x["T"] for x in rr], "o-", color=COL[impl], label=NAME[impl])
ax[0].loglog(ps, ps, "k--", label="идеал S=p")
ax[0].set_xticks(ps); ax[0].set_xticklabels(ps); ax[0].set_xlabel("число потоков / процессов p"); ax[0].set_ylabel("ускорение S(p)")
ax[0].set_title("Ускорение (лог. оси)"); ax[0].legend()
ax[1].set_xticks(ps); ax[1].set_xticklabels(ps); ax[1].set_xlabel("p"); ax[1].set_ylabel("время T(p), с"); ax[1].set_title("Время выполнения")
plt.tight_layout(); plt.savefig(FIG / "speedup.png"); plt.close()

# ---------- гибрид ----------
hy = parse("hybrid.txt", "RESULT")
S["hybrid"] = [dict(procs=int(r["procs"]), threads=int(r["threads"]), T=r["median"], Tmin=r["min"], Tmax=r["max"]) for r in hy]

# ---------- второй набор: задача в кэше ----------
sc2 = parse("scaling_cache.txt", "RESULT")
b2 = {r["impl"]: r["median"] for r in sc2 if tot(r) == 1}
rows2 = [dict(impl=r["impl"], p=tot(r), procs=int(r["procs"]), threads=int(r["threads"]), T=r["median"], Tmin=r["min"], Tmax=r["max"],
              S=b2[r["impl"]] / r["median"], E=b2[r["impl"]] / r["median"] / tot(r), S_abs=min(b2.values()) / r["median"]) for r in sc2]
S["scaling_cache"] = rows2
S["N2"] = int(sc2[0]["N"]); S["steps2"] = int(sc2[0]["steps"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
for impl in ("omp", "mpi", "hyb"):
    rr = sorted([x for x in rows2 if x["impl"] == impl], key=lambda x: x["p"])
    ax[0].loglog([x["p"] for x in rr], [x["S"] for x in rr], "o-", color=COL[impl], label=NAME[impl])
    ax[1].loglog([x["p"] for x in rr], [x["T"] for x in rr], "o-", color=COL[impl], label=NAME[impl])
ax[0].loglog(ps, ps, "k--", label="идеал S=p")
ax[0].set_xticks(ps); ax[0].set_xticklabels(ps); ax[0].set_xlabel("p"); ax[0].set_ylabel("ускорение S(p)"); ax[0].set_title("Задача в кэше: ускорение"); ax[0].legend()
ax[1].set_xticks(ps); ax[1].set_xticklabels(ps); ax[1].set_xlabel("p"); ax[1].set_ylabel("T(p), с"); ax[1].set_title("Задача в кэше: время")
plt.tight_layout(); plt.savefig(FIG / "speedup_cache.png"); plt.close()
hy2 = parse("hybrid_cache.txt", "RESULT")
S["hybrid_cache"] = [dict(procs=int(r["procs"]), threads=int(r["threads"]), T=r["median"], Tmin=r["min"], Tmax=r["max"]) for r in hy2]
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for a_, key, ttl in ((ax[0], "hybrid", "N=2^24 (память)"), (ax[1], "hybrid_cache", "N=2^20 (кэш)")):
    a_.bar([f"{h['procs']}×{h['threads']}" for h in S[key]], [h["T"] for h in S[key]], color=COL["hyb"])
    a_.set_xlabel("процессов × потоков"); a_.set_ylabel("T, с"); a_.set_title("Гибрид, " + ttl)
plt.tight_layout(); plt.savefig(FIG / "hybrid.png"); plt.close()

# ---------- память ----------
mem = parse("memory.txt", "RESULT")
mrows = {}
for r in mem:
    key = int(r["N"])
    cfg = {"omp": "omp16", "mpi": "mpi16", "hyb": "hyb2x8"}[r["impl"]]
    mrows.setdefault(key, {})[cfg] = r["rss_mb"]
S["memory"] = [dict(N=n, data_mb=2 * (n + 2) * 8 / 2**20, **v) for n, v in sorted(mrows.items())]
fig, ax = plt.subplots(figsize=(7, 4))
x = np.arange(len(S["memory"])); w = .27
for i, (cfg, c) in enumerate((("omp16", COL["omp"]), ("hyb2x8", COL["hyb"]), ("mpi16", COL["mpi"]))):
    ax.bar(x + (i - 1) * w, [m[cfg] for m in S["memory"]], w, color=c, label={"omp16": "1 процесс × 16 потоков", "hyb2x8": "2 × 8", "mpi16": "16 MPI-процессов"}[cfg])
ax.set_xticks(x); ax.set_xticklabels([f"N=2^{int(np.log2(m['N']))}" for m in S["memory"]])
ax.set_yscale("log"); ax.set_ylabel("суммарный RSS, МБ"); ax.set_title("Память: 16 процессов против 16 потоков"); ax.legend()
plt.tight_layout(); plt.savefig(FIG / "memory.png"); plt.close()

# ---------- ping-pong ----------
pp = parse("pingpong.txt", "PP")
M = np.array([r["bytes"] for r in pp]); T = np.array([r["time_us"] for r in pp]) * 1e-6
# метод наименьших квадратов с относительными весами 1/T (чтобы малые сообщения не терялись)
A = np.vstack([np.ones_like(M), M]).T
w = 1.0 / T
coef, *_ = np.linalg.lstsq(A * w[:, None], T * w, rcond=None)
ts, inv_b = coef
B = 1.0 / inv_b
pred = ts + M * inv_b
ss_res = np.sum(((T - pred) / T) ** 2)
S["pingpong"] = dict(ts_us=ts * 1e6, B_GBs=B / 1e9, Mstar=ts * B, t_1byte_us=T[0] * 1e6,
                     max_rel_err=float(np.max(np.abs(pred - T) / T)), rows=[dict(bytes=int(m), us=t * 1e6) for m, t in zip(M, T)])
# дополнительная подгонка только по крупным сообщениям (>=64 КБ) - канал упирается в пропускную способность
big = M >= 65536
cb, *_ = np.linalg.lstsq(A[big] * w[big, None], T[big] * w[big], rcond=None)
S["pingpong"]["ts_big_us"] = cb[0] * 1e6; S["pingpong"]["B_big_GBs"] = 1e-9 / cb[1]
mid = (M >= 4096) & (M <= 4194304)   # область «рабочих» сообщений: после смены протокола, пока данные в кэше
cm, *_ = np.linalg.lstsq(A[mid] * w[mid, None], T[mid] * w[mid], rcond=None)
S["pingpong"]["ts_mid_us"] = cm[0] * 1e6; S["pingpong"]["B_mid_GBs"] = 1e-9 / cm[1]
S["pingpong"]["mid_max_rel_err"] = float(np.max(np.abs(cm[0] + M[mid] * cm[1] - T[mid]) / T[mid]))
fig, ax = plt.subplots(figsize=(7, 4.3))
ax.loglog(M, T * 1e6, "o", color=COL["mpi"], label="измерено (медиана)")
mm = np.logspace(0, np.log10(M.max()), 200)
ax.loglog(mm, (ts + mm * inv_b) * 1e6, "k-", label=f"Tcomm = ts + M/B\nts={ts*1e6:.2f} мкс, B={B/1e9:.1f} ГБ/с")
ax.loglog(mm[mm >= 4096], (cm[0] + mm[mm >= 4096] * cm[1]) * 1e6, "--", color=COL["omp"], label=f"подгонка 4 КБ–4 МБ:\nts={cm[0]*1e6:.2f} мкс, B={1e-9/cm[1]:.1f} ГБ/с")
ax.axvline(ts * B, color="gray", ls=":", label=f"M* = ts·B ≈ {ts*B/1024:.1f} КБ")
ax.set_xlabel("длина сообщения M, байт"); ax.set_ylabel("время пересылки, мкс"); ax.legend(); ax.set_title("MPI ping-pong")
plt.tight_layout(); plt.savefig(FIG / "pingpong.png"); plt.close()

# ---------- false sharing ----------
S["falseshare"] = [dict(threads=int(r["threads"]), packed=r["packed"], padded=r["padded"], ratio=r["ratio"]) for r in parse("falseshare.txt", "FALSESHARE")]

# ---------- верификация ----------
vf = RES / "verify.txt"
S["verify"] = parse("verify.txt", "VERIFY") if vf.exists() else []
S["system"] = (RES / "system.txt").read_text(encoding="utf8")

(RES / "summary.json").write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf8")
print(json.dumps({k: S[k] for k in ("scaling", "hybrid", "memory", "falseshare")}, ensure_ascii=False, indent=1))
print({k: v for k, v in S["pingpong"].items() if k != "rows"})
