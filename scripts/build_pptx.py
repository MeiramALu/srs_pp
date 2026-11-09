"""Презентация для защиты: .venv\\Scripts\\python scripts\\build_pptx.py -> SIW2_Presentation.pptx"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "results/summary.json").read_text(encoding="utf8"))
FIG = ROOT / "figures"
pp = S["pingpong"]
sp = lambda key, impl, p: [r for r in S[key] if r["impl"] == impl and r["p"] == p][0]

NAVY, BLUE, RED, GREEN, GRAY, LIGHT = RGBColor(0x1F, 0x2A, 0x44), RGBColor(0x1F, 0x77, 0xB4), RGBColor(0xD6, 0x27, 0x28), RGBColor(0x2C, 0xA0, 0x2C), RGBColor(0x55, 0x5B, 0x66), RGBColor(0xF2, 0xF4, 0xF8)
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
blank = prs.slide_layouts[6]
FONT = "Calibri"


def tb(slide, x, y, w, h, text="", size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    p = tf.paragraphs[0]; p.alignment = align; r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = FONT
    return tf


def bullets(slide, x, y, w, h, items, size=18, color=NAVY, gap=6):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = s.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        bold_part, rest = (it.split("|", 1) + [""])[:2] if "|" in it else ("", it)
        r0 = p.add_run(); r0.text = "• " + (bold_part if bold_part else ""); r0.font.bold = True; r0.font.size = Pt(size); r0.font.color.rgb = color; r0.font.name = FONT
        r1 = p.add_run(); r1.text = rest if bold_part else it; r1.font.size = Pt(size); r1.font.color.rgb = color; r1.font.name = FONT
        if not bold_part: r0.text = "• "
    return tf


def new(title, notes="", sub=None):
    s = prs.slides.add_slide(blank)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05)); bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    tb(s, 0.5, 0.12, 12.3, 0.85, title, 30, True, RGBColor(255, 255, 255), anchor=MSO_ANCHOR.MIDDLE)
    n = len(prs.slides)
    tb(s, 12.3, 7.0, 0.8, 0.35, str(n), 11, False, GRAY, PP_ALIGN.RIGHT)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s


def card(slide, x, y, w, h, head, lines, color=BLUE, size=16):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); r.adjustments[0] = .04
    r.fill.solid(); r.fill.fore_color.rgb = LIGHT; r.line.color.rgb = color; r.line.width = Pt(1.5)
    tb(slide, x + .2, y + .1, w - .4, .5, head, 20, True, color)
    bullets(slide, x + .2, y + .65, w - .4, h - .8, lines, size, NAVY, 4)


def pic(slide, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    slide.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), **kw)


# 1 титул
s = prs.slides.add_slide(blank)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
tb(s, 0.9, 2.0, 11.5, 1.6, "Сравнение моделей параллельного программирования OpenMP и MPI", 40, True, RGBColor(255, 255, 255))
tb(s, 0.9, 4.0, 11.5, 1, "Эксперимент: одномерное уравнение теплопроводности — OpenMP, MPI и гибрид MPI + OpenMP", 22, False, RGBColor(0xC8, 0xD3, 0xE8))
tb(s, 0.9, 6.0, 11.5, 0.5, "SIW 2 · защита работы · 2026", 16, False, RGBColor(0xC8, 0xD3, 0xE8))
s.notes_slide.notes_text_frame.text = "Тема: сравнить две главные модели параллельного программирования не по описаниям, а по собственным измерениям на одной машине."

# 2 задача
s = new("Что требовалось сделать", "Задание — не пересказ стандартов, а эксперимент: один алгоритм реализован трижды, всё измерено на одной машине.")
bullets(s, .6, 1.4, 12.2, 5.5, [
    "Понять|  разницу моделей памяти: OpenMP — общая память, MPI — у каждого процесса своя.",
    "Реализовать|  один алгоритм трижды: OpenMP, MPI, гибрид MPI + OpenMP (ядро вычислений одно и то же).",
    "Проверить|  корректность: норма L∞ разности с последовательной программой.",
    "Измерить|  время, ускорение S(p) = T(1)/T(p), эффективность E(p) = S(p)/p для p = 1, 2, 4, 8, 16 (медиана 5+ прогонов, первый отброшен).",
    "Определить|  латентность t_s и пропускную способность B канала MPI по формуле T = t_s + M/B.",
    "Исследовать|  деления ресурса в гибриде (16×1, 8×2, 4×4, 2×8, 1×16) и расход памяти.",
    "Сделать вывод|  когда какая модель лучше — цифрами, а не общими словами.",
], 20, gap=10)

# 3 память
s = new("Главное различие: модель памяти", "Это единственное различие определяет почти всё остальное: где скрыта цена обмена, кто отвечает за корректность, как переносить на кластер.")
card(s, .6, 1.4, 6.0, 4.6, "OpenMP — общая память", [
    "Единое адресное пространство: любой поток видит все данные",
    "Обмен «бесплатен» в коде, но цена скрыта в железе: барьеры, когерентность кэшей",
    "Программист отвечает за гонки: private / shared, barrier, critical, atomic",
    "Предел — один узел"], BLUE)
card(s, 6.8, 1.4, 6.0, 4.6, "MPI — раздельная память", [
    "У каждого процесса своё адресное пространство",
    "Любой обмен — явный: Send/Recv, Bcast, Reduce",
    "Гонок между процессами нет, но каждое сообщение имеет цену t_s + M/B",
    "Работает на кластере: от ноутбука до суперкомпьютера"], RED)
tb(s, .6, 6.2, 12.2, .8, "Одно различие → разные модели исполнения, стоимости, отладки и масштабируемости", 20, True, NAVY, PP_ALIGN.CENTER)

# 4 исполнение
s = new("Модели исполнения", "OpenMP — fork-join: один поток, затем команда потоков, затем снова один. MPI — SPMD: все процессы с первой строки.")
card(s, .6, 1.4, 6.0, 4.9, "OpenMP: fork–join", [
    "Главный поток → параллельная область → барьер → снова один поток",
    "Конструкции разделения работы: omp for",
    "Без -fopenmp — корректная последовательная программа",
    "Можно распараллеливать по одному циклу (инкрементально)"], BLUE)
card(s, 6.8, 1.4, 6.0, 4.9, "MPI: SPMD", [
    "Все процессы исполняют один и тот же код от начала до конца",
    "Различие поведения — по рангу в коммуникаторе",
    "Параллельна с первой строки: «выключить» MPI нельзя",
    "Инкрементальный переход невозможен — нужна декомпозиция данных"], RED)

# 5 стоимость
s = new("Модели стоимости", "В модели общей памяти — синхронизация и когерентность; в распределённой — сообщение. Для коротких сообщений выигрыш от укрупнения.")
card(s, .6, 1.4, 6.0, 3.3, "Общая память", [
    "Барьеры, замки, atomic",
    "Трафик когерентности кэшей",
    "False sharing: потоки пишут в разные переменные одной строки кэша"], BLUE)
card(s, 6.8, 1.4, 6.0, 3.3, "Распределённая память", [
    "Сообщение: T = t_s + M / B",
    "t_s — латентность, B — пропускная способность",
    "M < t_s·B: платим латентность → укрупняем обмены"], RED)
tb(s, .6, 5.0, 12.2, .9, "T_comm = t_s + M / B", 40, True, NAVY, PP_ALIGN.CENTER)
tb(s, .6, 6.0, 12.2, .9, "В нашей задаче граничное сообщение — 8 байт ≪ t_s·B: обмен целиком определяется латентностью", 18, False, GRAY, PP_ALIGN.CENTER)

# 6 алгоритм
s = new("Алгоритм и три реализации", "Явная схема FTCS. Ядро kernel(a,b,lo,hi) общее для всех, поэтому сравнивается модель, а не арифметика.")
tb(s, .6, 1.3, 12.2, .7, "u_i(n+1) = u_i(n) + r·( u_(i−1)(n) − 2u_i(n) + u_(i+1)(n) ),   r = 0,25,  границы Дирихле", 22, True, NAVY, PP_ALIGN.CENTER)
card(s, .5, 2.2, 4.0, 4.4, "OpenMP", [
    "Блок индексов на поток",
    "Барьер между шагами",
    "Параллельная инициализация (first touch)",
    "Нет кода обмена"], BLUE, 16)
card(s, 4.67, 2.2, 4.0, 4.4, "MPI", [
    "Полосы по рангам",
    "Призрачные ячейки",
    "2× MPI_Sendrecv на шаг",
    "Gatherv — для проверки"], RED, 16)
card(s, 8.84, 2.2, 4.0, 4.4, "MPI + OpenMP", [
    "MPI_Init_thread(FUNNELED)",
    "Потоки считают блок",
    "Обмен — главный поток (master) между барьерами"], GREEN, 16)

# 7 стенд
s = new("Стенд и методика", "Важно честно назвать ограничения: WSL2, один узел, один NUMA-домен, шум Windows.")
bullets(s, .6, 1.4, 6.4, 5.5, [
    "Железо:|  Intel i5-13400F, 16 аппаратных потоков, L2 10 МиБ, L3 20 МиБ, ОЗУ 16 ГиБ",
    "ПО:|  WSL2 Ubuntu 24.04, gcc 13.3, Open MPI 4.1.6",
    "Размещение:|  явное, --bind-to hwthread, OMP_PROC_BIND=spread; проверено --report-bindings",
    "Прогоны:|  6 (режим А) / 11 (режим Б), первый отброшен, медиана + разброс",
], 18, gap=10)
card(s, 7.3, 1.4, 5.5, 2.5, "Режим А — память", ["N = 2^24 (256 МиБ), 100 шагов", "Не помещается в кэш"], BLUE, 16)
card(s, 7.3, 4.1, 5.5, 2.5, "Режим Б — кэш", ["N = 2^18 (4 МиБ), 8000 шагов", "Упор в синхронизацию"], GREEN, 16)

# 8 корректность
s = new("Корректность: норма L∞", "Результат совпал побитово: каждый узел считается одним выражением в одном порядке. Для задач с редукциями ожидается 1e-16…1e-12.")
tb(s, .6, 1.5, 12.2, 1.2, "L∞ = max |u_i − u_i(serial)| = 0", 48, True, GREEN, PP_ALIGN.CENTER)
bullets(s, 1.2, 3.2, 11, 3.5, [
    f"{len(S['verify'])} запусков:|  OpenMP p = 1…16, MPI p = 1…16, гибрид — 5 делений",
    "N = 1 000 003|  (не кратно числу процессов), 200 шагов",
    "Нулевая норма ожидаема:|  нет редукций, порядок операций в узле не зависит от разбиения",
], 22, gap=14)

# 9 режим А
a8o, a8m, a8h = sp("scaling", "omp", 8), sp("scaling", "mpi", 8), sp("scaling", "hyb", 8)
s = new("Результаты, режим А: упираемся в память", "Потолок ускорения ≈1,5 — это пропускная способность шины памяти, а не модель программирования.")
pic(s, "speedup.png", .4, 1.3, w=8.6)
bullets(s, 9.2, 1.5, 3.9, 5.5, [
    f"S(8):|  OpenMP {a8o['S']:.2f}, MPI {a8m['S']:.2f}, гибрид {a8h['S']:.2f}",
    "Потолок ≈ 1,5|  — шина памяти (≈ 34 ГБ/с уже у одного потока)",
    "При p = 16|  ускорение падает",
    "Три модели ≈ равны|  (разница 1–9 %)",
], 17, gap=12)

# 10 режим Б
b4, b8 = sp("scaling_cache", "omp", 4), sp("scaling_cache", "omp", 8)
s = new("Результаты, режим Б: данные в кэше", "Когда данные в кэше, ускорение лучше: S(8)≈4,1. p=16 шумный: два потока на ядро + Windows.")
pic(s, "speedup_cache.png", .4, 1.3, w=8.6)
bullets(s, 9.2, 1.5, 3.9, 5.5, [
    f"S(4) ≈ {b4['S']:.1f}  (E ≈ 0,8)",
    f"S(8) ≈ {b8['S']:.1f}  (E ≈ 0,5)",
    "Все три модели|  практически неотличимы до p = 8",
    "p = 16:|  деградация и огромный разброс — вывод низкой достоверности",
], 17, gap=12)

# 11 ping-pong
s = new("Латентность и пропускная способность MPI", "Open MPI меняет протокол около 4 КиБ, поэтому одна прямая описывает данные приближённо. Дали две подгонки.")
pic(s, "pingpong.png", .4, 1.3, w=7.6)
bullets(s, 8.3, 1.5, 4.7, 5.5, [
    f"t_s ≈ {pp['ts_us']:.2f} мкс|  (1 байт: {pp['t_1byte_us']:.2f} мкс)",
    f"B ≈ {pp['B_GBs']:.0f}–{pp['B_mid_GBs']:.0f} ГБ/с|  (через разделяемую память)",
    f"M* = t_s·B:|  ≈ {pp['Mstar']/1024:.0f} КиБ (все размеры) … ≈ {pp['ts_mid_us']*1e-6*pp['B_mid_GBs']*1e9/1024:.0f} КиБ (4 КиБ–4 МиБ)",
    "Граничное сообщение 8 Б|  ≪ M* → чистая латентность",
    "Это внутриузловой обмен,|  не кластерная сеть",
], 16, gap=10)

# 12 гибрид
hy = {(h["procs"], h["threads"]): h for h in S["hybrid"]}; hc = {(h["procs"], h["threads"]): h for h in S["hybrid_cache"]}
s = new("Гибрид: как делить 16 потоков", "На одном сокете без NUMA гибрид выигрыша по времени не даёт: нет границы сокета, а FUNNELED добавляет ожидание.")
pic(s, "hybrid.png", .4, 1.3, w=8.6)
bullets(s, 9.2, 1.5, 3.9, 5.5, [
    "Режим А:|  все деления 0,81–0,83 с — шина памяти",
    f"Режим Б:|  лучшее 16×1 ({hc[(16,1)]['T']:.2f} с), худшее 1×16 ({hc[(1,16)]['T']:.2f} с)",
    "Причина:|  один сокет, нет NUMA; FUNNELED — потоки ждут master; SMT",
    "Выигрыш гибрида|  — NUMA, память, число рангов на кластере",
], 16, gap=10)

# 13 память
mm = {m["N"]: m for m in S["memory"]}
s = new("Память: 16 процессов против 16 потоков", "Сами данные не дублируются, но каждый MPI-процесс несёт ≈15 МиБ среды выполнения. Для реплицируемых данных разница растёт.")
pic(s, "memory.png", .4, 1.3, w=7.4)
bullets(s, 8.0, 1.5, 5.0, 5.5, [
    f"N = 2^16:|  {mm[65536]['mpi16']:.0f} МиБ у MPI против {mm[65536]['omp16']:.1f} МиБ у OpenMP",
    f"N = 2^24:|  на {(mm[16777216]['mpi16']/mm[16777216]['omp16']-1)*100:.0f} % больше",
    f"N = 2^26:|  всего на {(mm[67108864]['mpi16']/mm[67108864]['omp16']-1)*100:.0f} %",
    "Разница ≈ 243 МиБ|  ≈ 15 МиБ × 16 процессов — постоянная цена процесса",
    "Решает|  при рабочем наборе ≲ 0,25–1 ГиБ на узел или при реплицируемых данных",
], 16, gap=10)

# 14 таблица
s = new("Сравнение по критериям (кратко)", "Полная таблица с развёрнутыми утверждениями — в отчёте, раздел 4.1.")
rows = [("Критерий", "OpenMP", "MPI"),
        ("Память", "Общая; видят все, риск гонок", "Раздельная; всё явно"),
        ("Коммуникация", "Неявная: барьеры, когерентность", "Сообщения: t_s + M/B"),
        ("Гранулярность", "Мелкая / средняя", "Крупная"),
        ("Предел масштаба", "Один узел (шина памяти)", "Многоузловой; сеть, коллективы"),
        ("Инкрементальность", "Да, по директиве", "Нет"),
        ("Отладка", "Один процесс; гонки, false sharing", "Deadlock Send/Recv; N процессов"),
        ("Переносимость", "Корректность — да, скорость — хуже", "От ноутбука до суперкомпьютера")]
t = s.shapes.add_table(len(rows), 3, Inches(.6), Inches(1.4), Inches(12.1), Inches(5.2)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = t.cell(i, j); c.text = v
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(16 if i else 17); r.font.bold = (i == 0 or j == 0); r.font.name = FONT
                r.font.color.rgb = RGBColor(255, 255, 255) if i == 0 else NAVY
        c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (LIGHT if i % 2 else RGBColor(255, 255, 255))
t.columns[0].width = Inches(2.8); t.columns[1].width = Inches(4.7); t.columns[2].width = Inches(4.6)

# 15 выводы
s = new("Выводы: какую модель выбрать", "Выбор — по соответствию модели памяти машины, подкреплённый нашими цифрами для одного узла; многоузловой режим не измерялся.")
card(s, .6, 1.4, 4.0, 4.7, "OpenMP", ["Один узел, данные ≲ 1 ГиБ", "Время равно MPI (p = 8: 0,76 с vs 0,83 с; режим Б: 0,164 vs 0,165 с)", "Код проще, память меньше"], BLUE, 16)
card(s, 4.67, 1.4, 4.0, 4.7, "MPI", ["Несколько узлов / кластер", "Явная локальность", "Не медленнее OpenMP на узле"], RED, 16)
card(s, 8.74, 1.4, 4.0, 4.7, "Гибрид", ["Несколько NUMA / сокетов", "Мало памяти на узел", "Много рангов на кластере"], GREEN, 16)
tb(s, .6, 6.3, 12.2, .7, "Железо (шина памяти, SMT) повлияло на результат сильнее, чем выбор модели", 20, True, NAVY, PP_ALIGN.CENTER)

# 16 ускорители и ограничения
s = new("Ускорители и ограничения работы", "Третий уровень: MPI между узлами, OpenMP на ядрах, GPU через CUDA/HIP/target/SYCL. Узкое место — перенос данных.")
card(s, .6, 1.4, 6.0, 5.0, "Узлы с ускорителями", [
    "Третий уровень параллелизма: MPI → потоки → ядра GPU (CUDA/HIP, OpenMP target, SYCL)",
    "Своя память у устройства → обмен хост↔устройство становится узким местом",
    "MPI остаётся межузловым уровнем (GPU-aware MPI)",
    "«MPI + X» — норма, а не исключение"], BLUE, 16)
card(s, 6.8, 1.4, 6.0, 5.0, "Ограничения эксперимента", [
    "WSL2, один узел, один NUMA → first touch и кластер не измерены",
    "MPI через разделяемую память: t_s, B — внутриузловые",
    "p = 16 шумный (SMT + Windows)",
    "Тест false sharing упрощён (до ×1,9)",
    "Всё воспроизводимо: scripts/run_all.sh"], RED, 16)

# 17 вопросы
s = new("Возможные вопросы на защите", "Короткие ответы для подготовки.")
bullets(s, .6, 1.3, 12.2, 5.8, [
    "Почему L∞ = 0?|  Один и тот же порядок операций в каждом узле, редукций нет.",
    "Почему ускорение всего 1,5 в режиме А?|  Задача упирается в пропускную способность памяти: ≈ 24 Б трафика на узел.",
    "Почему гибрид не выиграл?|  Один сокет, нет NUMA; FUNNELED добавляет ожидание. Выигрыш — на кластере/NUMA и по памяти.",
    "Что значит M*?|  Длина, при которой t_s = M/B; короче — платим латентность, длиннее — пропускную способность.",
    "Почему MPI съел 248 МиБ при крошечной задаче?|  ≈ 15 МиБ на процесс — среда выполнения.",
    "Что не измерено?|  Многоузловой режим, first touch на NUMA.",
], 17, gap=10)

out = ROOT / "SIW2_Presentation.pptx"; prs.save(out); print("saved", out, len(prs.slides), "slides")
