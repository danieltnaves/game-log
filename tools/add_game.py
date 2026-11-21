#!/usr/bin/env python3
"""Add, update or remove a game in games.json (cover, trailer and screenshots come from RAWG).

Examples
  python3 tools/add_game.py "Hades" --update --finished 2026-10-20 --notes "Played twice"
  python3 tools/add_game.py "Sekiro: Shadows Die Twice" --update --status Done --finished 2026-11-02
  python3 tools/add_game.py "Hades" --update --refresh --rawg-id 274755
  python3 tools/add_game.py "Hades" --remove
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


def find_game(games, title):
    """Return the index of the game matching the title (by id, then by title), or exit."""
    slug = slugify(title)
    for i, g in enumerate(games):
        if g.get("id") == slug or g.get("title", "").lower() == title.lower():
            return i
    close = difflib.get_close_matches(title, [g.get("title", "") for g in games], n=3, cutoff=0.5)
    hint = " Did you mean: %s?" % ", ".join("'%s'" % c for c in close) if close else ""
    sys.exit("'%s' is not in games.json.%s" % (title, hint))


def media_from_rawg(key, game_id):
    detail = rawg("games/%d" % game_id, key)
    movies = rawg("games/%d/movies" % game_id, key).get("results", [])
    shots = rawg("games/%d/screenshots" % game_id, key).get("results", [])
    return {
        "cover": detail.get("background_image") or "",
        "trailer": (movies[0]["data"].get("max") or movies[0]["data"].get("480") or "") if movies else "",
        "trailerPreview": movies[0].get("preview", "") if movies else "",
        "screenshots": [x["image"] for x in shots[:8]],
    }


def pick_rawg_id(key, title, rawg_id):
    if rawg_id:
        return rawg_id
    results = rawg("games", key, search=title, page_size=8)["results"]
    if not results:
        sys.exit("RAWG found nothing for that title. Try another spelling or add the game by hand.")
    best = max(results, key=lambda r: difflib.SequenceMatcher(None, norm(title), norm(r["name"])).ratio())
    print("Using RAWG match: %s (%s), id %d. If that is wrong, run again with --rawg-id." % (
        best["name"], (best.get("released") or "?")[:4], best["id"]))
    return best["id"]


def save(games):
    with open(GAMES, "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=1)
        f.write("\n")
    import build_site  # lives next to this script; rebuilds index.html from games.json
    build_site.main()


def main():
    ap = argparse.ArgumentParser(description="Add, update or remove a game in games.json.")
    ap.add_argument("title", help="game title (for --update and --remove it must match a game in games.json)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--update", action="store_true", help="change fields of a game that is already in games.json")
    mode.add_argument("--remove", action="store_true", help="remove the game from games.json")
    mode.add_argument("--search", action="store_true", help="only list RAWG matches and exit")
    ap.add_argument("--platform", default="", help="platform you played on, e.g. PS5, SNES, PC")
    ap.add_argument("--genre", default="", help="genre text shown on the page")
    ap.add_argument("--finished", default="", help="date finished, YYYY-MM-DD")
    ap.add_argument("--status", default="", help='"In progress" for unfinished games; "Done" marks a game as finished')
    ap.add_argument("--notes", default=None, help="short note shown under the game")
    ap.add_argument("--rawg-id", type=int, help="exact RAWG game id (skip the search)")
    ap.add_argument("--refresh", action="store_true", help="with --update: fetch the cover, trailer and screenshots again from RAWG")
    a = ap.parse_args()

    if a.search:
        for r in rawg("games", api_key(), search=a.title, page_size=8)["results"]:
            plats = ", ".join(p["platform"]["name"] for p in (r.get("platforms") or [])[:4])
            print("%8d  %-45s %s  %s" % (r["id"], r["name"][:45], (r.get("released") or "")[:4], plats))
        return

    if a.finished and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.finished):
        sys.exit("--finished must look like 2026-08-27")
    done = a.status.strip().lower() in ("done", "finished", "completed")

    games = json.load(open(GAMES, encoding="utf-8")) if os.path.exists(GAMES) else []

    if a.remove:
        removed = games.pop(find_game(games, a.title))
        save(games)
        print("Removed '%s'. %d game(s) left." % (removed["title"], len(games)))
        return

    if a.update:
        g = games[find_game(games, a.title)]
        if a.platform:
            g["platform"] = a.platform
        if a.genre:
            g["genre"] = a.genre
        if a.notes is not None:
            g["notes"] = a.notes
        if a.finished:
            g["finished"] = a.finished
        if done:
            g.pop("status", None)
        elif a.status:
            g["status"] = a.status
        if not g.get("status") and not g.get("finished"):
            sys.exit("A finished game needs a date. Add --finished YYYY-MM-DD.")
        if g.get("status") and not a.finished and done is False and a.status:
            g["finished"] = ""
        if a.refresh or a.rawg_id:
            g.update(media_from_rawg(api_key(), pick_rawg_id(api_key(), g["title"], a.rawg_id)))
        save(games)
        print("Updated '%s'." % g["title"])
        return

    # add
    if not a.finished and not a.status:
        sys.exit('Give --finished YYYY-MM-DD, or --status "In progress".')
    key = api_key()
    entry = {"id": slugify(a.title), "title": a.title, "platform": a.platform, "genre": a.genre, "finished": a.finished}
    if a.status and not done:
        entry["status"] = a.status
    entry["notes"] = a.notes or ""
    entry.update(media_from_rawg(key, pick_rawg_id(key, a.title, a.rawg_id)))
    if any(g.get("id") == entry["id"] for g in games):
        sys.exit("'%s' is already in games.json. Use --update to change it, or --remove first." % a.title)
    games.append(entry)
    save(games)
    print("Added '%s': cover %s, trailer %s, %d screenshot(s)." % (
        a.title, "yes" if entry["cover"] else "no", "yes" if entry["trailer"] else "no", len(entry["screenshots"])))


if __name__ == "__main__":
    main()
