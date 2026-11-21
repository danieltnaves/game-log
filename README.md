# Game Log

A static website that lists the games I have finished, with cover, details, trailer and screenshots.
No build step and no framework: plain HTML, CSS and JavaScript, ready for GitHub Pages.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The game list page. Click a game to see its trailer and screenshots. |
| `games.json` | All the game data. This is the only file you edit to change the list. |
| `docs.html` | Help page that explains how to add games (linked from the footer). |
| `covers/` | Cover images that are stored in this project. |
| `tools/add_game.py` | Script that adds a game using the RAWG API. |
| `.env.example` | Template for the RAWG key. Copy it to `.env`. |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are. |

## Add a game

1. Get a free key at <https://rawg.io/apidocs> and save it in a `.env` file:

   ```
   RAWG_API_KEY=your-key-here
   ```

   `.env` is in `.gitignore`. Never commit it.

2. Run the script:

   ```
   python3 tools/add_game.py "Hades" --platform PS5 --genre "Roguelike" --finished 2026-10-12
   ```

   For a game you have not finished, use `--status "In progress"` instead of `--finished`.
   If the wrong game is matched, run `--search` to list RAWG matches and pass `--rawg-id`.

You can also edit `games.json` by hand. The full field list and more examples are in [`docs.html`](docs.html).

## Preview locally

The page loads `games.json`, so open it through a web server:

```
python3 -m http.server 8000
```

Then visit <http://localhost:8000>.

## Publish on GitHub Pages

1. Push this folder to a GitHub repository (without `.env`).
2. Go to **Settings, Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`.
3. The site appears at `https://YOUR-USER.github.io/YOUR-REPO/`.

## Credits

Game data and images come from [RAWG](https://rawg.io).
