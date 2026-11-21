#!/usr/bin/env python3
"""Add a game to games.json using the RAWG API (cover, trailer, screenshots).

Examples
  python3 tools/add_game.py "Hades" --search
  python3 tools/add_game.py "Hades" --platform PS5 --genre "Roguelike" --finished 2026-10-12
  python3 tools/add_game.py "Sekiro" --platform PS4 --genre "Souls Like" --status "In progress"
  python3 tools/add_game.py "Dark Souls III" --rawg-id 12345 --platform PS5 --genre "Souls Like" --finished 2026-08-27

The RAWG key is read from the RAWG_API_KEY environment variable or from the
.env file in the project root. Only the Python standard library is used.
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES = os.path.join(ROOT, "games.json")
HEADERS = {"User-Agent": "game-log-add-game/1.0"}


def api_key():
    key = os.environ.get("RAWG_API_KEY", "").strip()
    env = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.startswith("RAWG_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("No RAWG key found. Put RAWG_API_KEY=... in the .env file (see .env.example).")
    return key


def rawg(path, key, **params):
    params["key"] = key
    url = "https://api.rawg.io/api/%s?%s" % (path, urllib.parse.urlencode(params))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit("RAWG rejected the API key (HTTP %d)." % e.code)
            time.sleep(2 * (attempt + 1))
        except urllib.error.URLError:
            time.sleep(2 * (attempt + 1))
    sys.exit("Could not reach RAWG. Check your connection and try again.")


def norm(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower().replace("&", "and"))


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    ap = argparse.ArgumentParser(description="Add a game to games.json using RAWG.")
    ap.add_argument("title", help="game title (also used to search RAWG)")
    ap.add_argument("--platform", default="", help="platform you played on, e.g. PS5, SNES, PC")
    ap.add_argument("--genre", default="", help="genre text shown on the page")
    ap.add_argument("--finished", default="", help="date finished, YYYY-MM-DD")
    ap.add_argument("--status", default="", help='use "In progress" for games you have not finished')
    ap.add_argument("--notes", default="", help="short note shown under the game")
    ap.add_argument("--rawg-id", type=int, help="exact RAWG game id (skip the search)")
    ap.add_argument("--search", action="store_true", help="only list RAWG matches and exit")
    ap.add_argument("--replace", action="store_true", help="replace the game if it is already in games.json")
    a = ap.parse_args()

    key = api_key()

    if a.search:
        for r in rawg("games", key, search=a.title, page_size=8)["results"]:
            plats = ", ".join(p["platform"]["name"] for p in (r.get("platforms") or [])[:4])
            print("%8d  %-45s %s  %s" % (r["id"], r["name"][:45], (r.get("released") or "")[:4], plats))
        return

    if a.finished and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.finished):
        sys.exit("--finished must look like 2026-08-27")
    if not a.finished and not a.status:
        sys.exit('Give --finished YYYY-MM-DD, or --status "In progress".')

    if a.rawg_id:
        game_id = a.rawg_id
    else:
        results = rawg("games", key, search=a.title, page_size=8)["results"]
        if not results:
            sys.exit("RAWG found nothing for that title. Try another spelling or add the game by hand.")
        best = max(results, key=lambda r: difflib.SequenceMatcher(None, norm(a.title), norm(r["name"])).ratio())
        game_id = best["id"]
        print("Using RAWG match: %s (%s), id %d. If that is wrong, run again with --rawg-id." % (
            best["name"], (best.get("released") or "?")[:4], game_id))

    detail = rawg("games/%d" % game_id, key)
    movies = rawg("games/%d/movies" % game_id, key).get("results", [])
    shots = rawg("games/%d/screenshots" % game_id, key).get("results", [])

    entry = {
        "id": slugify(a.title),
        "title": a.title,
        "platform": a.platform,
        "genre": a.genre,
        "finished": a.finished,
    }
    if a.status:
        entry["status"] = a.status
    entry.update({
        "notes": a.notes,
        "cover": detail.get("background_image") or "",
        "trailer": (movies[0]["data"].get("max") or movies[0]["data"].get("480") or "") if movies else "",
        "trailerPreview": movies[0].get("preview", "") if movies else "",
        "screenshots": [s["image"] for s in shots[:8]],
    })

    games = json.load(open(GAMES, encoding="utf-8")) if os.path.exists(GAMES) else []
    existing = [i for i, g in enumerate(games) if g.get("id") == entry["id"]]
    if existing and not a.replace:
        sys.exit("'%s' is already in games.json. Use --replace to overwrite it." % a.title)
    if existing:
        games[existing[0]] = entry
    else:
        games.append(entry)

    with open(GAMES, "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("Added '%s': cover %s, trailer %s, %d screenshot(s)." % (
        a.title, "yes" if entry["cover"] else "no", "yes" if entry["trailer"] else "no", len(entry["screenshots"])))


if __name__ == "__main__":
    main()
