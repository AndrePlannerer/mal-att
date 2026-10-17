#!/usr/bin/env python3
"""Gera os gráficos do perfil do MyAnimeList (PNG) a partir da lista pública.

Uso:
  python scripts/build.py                 # busca dados ao vivo
  python scripts/build.py --data lista.json   # usa um JSON local (teste)
"""
import argparse, json, os, sys, time, urllib.request
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

USER = os.environ.get("MAL_USER", "Vleber_23")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "charts")
STATS_FILE = os.path.join(ROOT, "stats.json")

BG, INK, MUTED, ORANGE = "#141414", "#E8E8E8", "#8A8A8A", "#F28C38"
UA = {"User-Agent": "Mozilla/5.0 (mal-att profile charts)"}


def get_json(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise last


def load_list():
    items, offset = [], 0
    while True:
        page = get_json(f"https://myanimelist.net/animelist/{USER}/load.json?status=7&offset={offset}")
        if not page:
            break
        items += page
        offset += len(page)
        time.sleep(0.5)
    return items


def jikan_extra():
    """Totais oficiais do perfil (dias, capítulos, episódios, completos) — best effort."""
    out = {}
    try:
        d = get_json(f"https://api.jikan.moe/v4/users/{USER}/statistics")["data"]
        out["days"] = round(float(d["anime"]["days_watched"]))
        out["chapters"] = int(d["manga"]["chapters_read"])
        out["episodes"] = int(d["anime"]["episodes_watched"])
        out["animes"] = int(d["anime"]["completed"])
    except Exception as e:  # noqa
        print("aviso: Jikan indisponível:", e, file=sys.stderr)
        out["_erro"] = repr(e)[:300]
    return out


def setup_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": INK, "axes.edgecolor": BG,
    })


def fmt(n):
    return f"{n:,}".replace(",", ".")


def chart_scores(scores):
    counts = [scores.get(i, 0) for i in range(1, 11)]
    peak = counts.index(max(counts))
    colors = ["#333", "#333", "#333", "#333", "#444", "#555", "#555", "#555", "#444", ORANGE]
    colors[peak] = "#8A8A8A"
    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=200)
    bars = ax.bar(range(1, 11), counts, width=0.74, color=colors)
    for b, c in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, c + max(counts) * 0.02, str(c),
                ha="center", va="bottom", fontsize=9, color=INK if c in (max(counts), counts[9]) else MUTED)
    ax.set_xticks(range(1, 11))
    ax.tick_params(axis="x", colors=MUTED, length=0, labelsize=10)
    ax.set_yticks([])
    ax.set_ylim(0, max(counts) * 1.18)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.subplots_adjust(left=0.04, right=0.96, top=0.93, bottom=0.12)
    fig.savefig(os.path.join(OUT, "scores.png"))
    plt.close(fig)


def chart_genres(genres, top=6):
    items = genres.most_common(top)[::-1]
    names = [n for n, _ in items]
    vals = [v for _, v in items]
    colors = ["#555"] * len(vals)
    colors[-1] = ORANGE
    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=200)
    bars = ax.barh(names, vals, height=0.62, color=colors)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.015, b.get_y() + b.get_height() / 2, str(v),
                va="center", fontsize=10, color=INK)
    ax.tick_params(axis="y", colors=INK, length=0, labelsize=11)
    ax.set_xticks([])
    ax.set_xlim(0, max(vals) * 1.15)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.subplots_adjust(left=0.2, right=0.96, top=0.95, bottom=0.05)
    fig.savefig(os.path.join(OUT, "genres.png"))
    plt.close(fig)


def chart_stats(st):
    tiles = [("animes", fmt(st["animes"])), ("episódios", fmt(st["episodes"])),
             ("dias de anime", fmt(st["days"])), ("capítulos", fmt(st["chapters"]))]
    fig = plt.figure(figsize=(6, 1.1), dpi=200)
    for i, (label, val) in enumerate(tiles):
        x = 0.125 + i * 0.25
        fig.text(x, 0.58, val, ha="center", va="center", fontsize=19, fontweight="bold",
                 color=ORANGE if i == 2 else INK)
        fig.text(x, 0.2, label, ha="center", va="center", fontsize=8.5, color=MUTED)
        if i:
            fig.add_artist(plt.Line2D([i * 0.25] * 2, [0.15, 0.85], color="#2a2a2a", lw=1))
    fig.savefig(os.path.join(OUT, "stats.png"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--no-jikan", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    setup_style()

    old = json.load(open(STATS_FILE)) if os.path.exists(STATS_FILE) else {}
    items = json.load(open(args.data)) if args.data else load_list()
    if not items:
        sys.exit("lista vazia; mantendo imagens anteriores")

    scores = Counter(int(i["score"]) for i in items if int(i.get("score") or 0) > 0)
    completed = [i for i in items if i.get("status") == 2]
    genres = Counter(g["name"] for i in completed for g in (i.get("genres") or []))
    st = {
        "animes": len(completed),
        "episodes": sum(int(i.get("num_watched_episodes") or 0) for i in items),
        "days": old.get("days", 356), "chapters": old.get("chapters", 35158),
    }
    if not args.data and not args.no_jikan:
        extra = jikan_extra()
        erro = extra.pop("_erro", None)
        st.update(extra)
        json.dump({"jikan_ok": erro is None, "erro": erro},
                  open(os.path.join(ROOT, "status.json"), "w"), indent=2, ensure_ascii=False)

    chart_scores(scores)
    if genres:
        chart_genres(genres)
    chart_stats(st)
    json.dump(st, open(STATS_FILE, "w"), indent=2, ensure_ascii=False)
    print("ok", st)


if __name__ == "__main__":
    main()
