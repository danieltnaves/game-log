#!/usr/bin/env python3
"""Build index.html, the game log page, from games.json (1990s style).

index.html is generated. Do not edit it by hand: change games.json and run this script.

Pure HTML only: no CSS (no <style>, no style="..."), no JavaScript. Everything
comes from old presentational tags and attributes (bgcolor, font, center, table
border, hr, marquee). Data is read from games.json and written into the page,
so the page needs no fetch and works when opened straight from disk.

Usage: python3 tools/build_site.py
(tools/add_game.py runs it automatically after every add, update or remove.)
"""
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = html.escape


def sort_key(g):
    # in-progress first, then newest finished first
    return (0 if g.get("status") else 1, "".join(chr(255 - ord(c)) for c in (g.get("finished") or "")))


def when(g):
    if g.get("status"):
        return "<i>%s</i>" % e(g["status"])
    f = g.get("finished") or ""
    try:
        return datetime.date.fromisoformat(f).strftime("%d %b %Y")
    except ValueError:
        return "-"


def main():
    games = json.load(open(os.path.join(ROOT, "games.json"), encoding="utf-8"))
    # same order as the main page: in progress first, newest first, later entries first on the same date
    games = [g for _, g in sorted(enumerate(games), key=lambda t: (sort_key(t[1]), -t[0]))]
    today = datetime.date.today().strftime("%d %B %Y")
    out = []
    w = out.append

    w('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">')
    w("<html>")
    w("<head>")
    w('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    w("<title>Game Log - Welcome to my home page!</title>")
    w("</head>")
    w('<body bgcolor="#C0C0C0" text="#000000" link="#0000EE" vlink="#551A8B" alink="#FF0000">')
    w("<center>")
    w('<table border="4" cellpadding="8" cellspacing="0" bgcolor="#000080" width="90%"><tr><td align="center">')
    w('<h1><font color="#FFFF00" face="Courier New, Courier, monospace">*** GAME LOG ***</font></h1>')
    w('<marquee width="80%" bgcolor="#000000"><font color="#00FF00" face="Courier New, Courier, monospace">'
      "Welcome to my page! Every game I have played, with pictures! Click a title for screenshots and trailers!"
      "</font></marquee>")
    w("</td></tr></table>")
    w("<p><font size=\"2\">Last updated: %s &nbsp;|&nbsp; %d games in the list</font></p>" % (e(today), len(games)))
    w("</center>")
    w('<hr noshade size="3">')

    # --- the list: cover on the left, everything about the game on the right (no links, no anchors)
    w("<center>")
    w('<h2><font color="#800000">The List</font></h2>')
    w('<table border="2" cellpadding="8" cellspacing="0" bgcolor="#FFFFFF" width="95%">')
    w('<tr bgcolor="#000080">'
      '<th width="280"><font color="#FFFFFF">Cover</font></th>'
      '<th><font color="#FFFFFF">Game</font></th></tr>')
    for i, g in enumerate(games):
        bg = "#FFFFFF" if i % 2 == 0 else "#E8E8FF"
        cover = g.get("cover") or ""
        img = ('<img src="%s" width="260" border="1" alt="Cover of %s">' % (e(cover), e(g["title"]))
               if cover else "<tt>[no picture]</tt>")
        w('<tr bgcolor="%s" valign="top">' % bg)
        w('<td align="center">%s</td>' % img)
        w("<td>")
        w('<font size="5" color="#000080"><b>%s</b></font>' % e(g["title"]))
        w('<table border="0" cellpadding="2" cellspacing="0">')
        w("<tr><td><b>Platform:</b></td><td>%s</td></tr>" % e(g.get("platform") or "-"))
        w("<tr><td><b>Genre:</b></td><td>%s</td></tr>" % e(g.get("genre") or "-"))
        w("<tr><td><b>%s:</b></td><td>%s</td></tr>" % ("Status" if g.get("status") else "Finished", when(g)))
        if g.get("notes"):
            w("<tr><td><b>Notes:</b></td><td>%s</td></tr>" % e(g["notes"]))
        w("</table>")
        if g.get("trailer"):
            w("<p><b>Trailer:</b><br>")
            w('<video controls preload="none" width="480"%s src="%s">Your browser cannot play video.</video></p>' % (
                ' poster="%s"' % e(g["trailerPreview"]) if g.get("trailerPreview") else "", e(g["trailer"])))
        shots = g.get("screenshots") or []
        if shots:
            w("<p><b>Screenshots</b> (click one to see it full size):</p>")
            w('<table border="0" cellpadding="3" cellspacing="0"><tr>')
            for n, x in enumerate(shots):
                if n and n % 3 == 0:
                    w("</tr><tr>")
                w('<td><a href="%s" target="_blank"><img src="%s" width="200" border="1" alt="Screenshot %d of %s" loading="lazy"></a></td>' % (
                    e(x), e(x), n + 1, e(g["title"])))
            w("</tr></table>")
        else:
            w("<p><i>No screenshots for this one, sorry!</i></p>")
        w("</td>")
        w("</tr>")
    w("</table>")
    w("</center>")

    # --- footer
    w('<hr noshade size="3">')
    w("<center>")
    w('<font size="2">')
    w('Pictures and trailers from <a href="https://rawg.io">RAWG</a>.<br>')
    w('<a href="docs.html">How to add games</a><br><br>')
    w("<b>This page is best viewed with ANY browser, at any screen size.</b><br>")
    w("Made with Notepad. No frames, no JavaScript, no style sheets.")
    w("</font>")
    w("</center>")
    w("</body>")
    w("</html>")

    path = os.path.join(ROOT, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("Wrote %s (%d games)" % (path, len(games)))


if __name__ == "__main__":
    main()
