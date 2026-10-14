"""Count U-Bahn routes Heiligenstadt -> Stephansplatz that never reuse a line.

Network: Wiener Linien open data (lines, stops, stop sequences per line),
treated as fully open (no closures). A route is a sequence of rides
(line, board, alight); you may change lines only at a station both lines serve.
"""
import csv
import io
import sys
import urllib.request

OGD = "https://www.wienerlinien.at/ogd_realtime/doku/ogd/"
START, GOAL = "Heiligenstadt", "Stephansplatz"


def load(name):
    with urllib.request.urlopen(OGD + name) as r:
        text = r.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def network():
    metro = {r["LineID"]: r["LineText"] for r in load("wienerlinien-ogd-linien.csv")
             if r["MeansOfTransport"] == "ptMetro"}
    stop = {r["StopID"]: r["StopText"].replace("Meidling, Hauptstraße", "Meidling Hauptstraße")
            for r in load("wienerlinien-ogd-haltepunkte.csv")}
    seqs = {}
    for r in load("wienerlinien-ogd-fahrwegverlaeufe.csv"):
        if r["LineID"] in metro and r["PatternID"] == "1" and r["Direction"] == "1":
            seqs.setdefault(metro[r["LineID"]], []).append((int(r["StopSeqCount"]), stop[r["StopID"]]))
    return {line: [s for _, s in sorted(v)] for line, v in sorted(seqs.items())}


def rides(lines, used, at):
    """Every single-line ride from `at` on a line not yet used: (line, stations passed incl. both ends)."""
    for line, stations in lines.items():
        if line in used or at not in stations:
            continue
        i = stations.index(at)
        for j in range(len(stations)):
            if j != i:
                step = 1 if j > i else -1
                yield line, stations[i:j + step:step] if j > i else stations[j:i + 1][::-1]


def enumerate_routes(lines, strict):
    """strict: no station may be visited (or passed through) twice."""
    out = []

    def dfs(at, used, seen, legs):
        for line, path in rides(lines, used, at):
            if strict and seen.intersection(path[1:]):
                continue
            leg = legs + [(line, path[0], path[-1])]
            if path[-1] == GOAL:
                out.append(leg)
            dfs(path[-1], used | {line}, seen | set(path), leg)

    dfs(START, frozenset(), {START}, [])
    return out


def fmt(route):
    return f"{route[0][1]} " + " ".join(f"-{l}-> {b}" for l, _, b in route)


if __name__ == "__main__":
    lines = network()
    for line, st in lines.items():
        print(f"{line}: {' - '.join(st)}")
    strict = enumerate_routes(lines, strict=True)
    print(f"\nRoutes, no line twice AND no station twice: {len(strict)}")
    for r in sorted(strict, key=lambda r: (len(r), fmt(r))):
        print("  " + fmt(r))
    loose = enumerate_routes(lines, strict=False)
    print(f"\nRoutes, no line twice (stations may repeat): {len(loose)}")
    if "-v" in sys.argv:
        for r in sorted(loose, key=lambda r: (len(r), fmt(r))):
            print("  " + fmt(r))
