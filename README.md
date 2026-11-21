# Game Log

A static website that lists the games I have played, with cover, details, trailer and screenshots.
It is written in plain 1990s-style HTML: no CSS, no JavaScript, no framework. Ready for GitHub Pages.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The game list page. **Generated** from `games.json`: do not edit it by hand. |
| `games.json` | All the game data. This is the file you change. |
| `docs.html` | Help page that explains how to add games (linked from the page footer). |
| `covers/` | Cover images that are stored in this project. |
| `tools/add_game.py` | Adds, updates and removes games (uses the RAWG API for covers and media). Rebuilds `index.html` afterwards. |
| `tools/build_site.py` | Builds `index.html` from `games.json`. |
| `.env.example` | Template for the RAWG key. Copy it to `.env`. |
| `.github/workflows/pages.yml` | Workflow that adds, updates and removes games from a form on GitHub and publishes the site. |
| `.nojekyll` | Keeps GitHub from processing the files with Jekyll. |

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

Update or remove a game with the same script:

```
python3 tools/add_game.py "Hades" --update --status Done --finished 2026-10-20
python3 tools/add_game.py "Hades" --remove
```

### Manage games from GitHub

The workflow in `.github/workflows/pages.yml` runs the same script from the browser:

1. One time: add your RAWG key as a repository secret named `RAWG_API_KEY` (**Settings, Secrets and variables, Actions**).
2. Open the **Actions** tab, choose **Manage games and deploy**, press **Run workflow**, pick an action (`add`, `update`, `remove` or `search`) and fill in the form.
3. The workflow commits the change to `games.json` and publishes the site.

You can also edit `games.json` by hand, then run `python3 tools/build_site.py` to rebuild `index.html`. The full field list and more examples are in [`docs.html`](docs.html).

## Preview locally

The data is inside `index.html`, so just open the file in your browser. You need an internet connection to see the pictures, which come from RAWG.

## Publish on GitHub Pages

1. Push this folder to a GitHub repository (without `.env`). Every push to `main` publishes the site.
2. Go to **Settings, Pages** and set **Source** to **GitHub Actions**.
3. The site appears at `https://YOUR-USER.github.io/YOUR-REPO/`.

## Credits

Game data and images come from [RAWG](https://rawg.io).
