# Publishing on the Tessera Marketplace

Tessera reads `marketplace.json` at the root of this repository.

## marketplace.json

```json
{
  "name": "My Marketplace",
  "plugins": [
    {
      "id": "author.plugin",
      "name": "My Plugin",
      "author": "Me",
      "version": "1.0.0",
      "description": "What it does.",
      "icon": "puzzle",
      "homepage": "https://github.com/me/my-plugin",
      "download": "https://example.com/author.plugin-1.0.0.tessera-plugin",
      "sha256": "<sha256 of the .tessera-plugin file>"
    }
  ]
}
```

- `id`, `name`, `version`, `download` and `sha256` are required. Entries missing them are skipped.
- `download` must be an `https` link to a package built with `tessera-plugin pack`.
- `sha256` is the hash of that file. Tessera refuses the install if it does not match.
- `icon` is a [Bootstrap Icons](https://icons.getbootstrap.com) name.

## Adding a plugin

1. Build the package: `npm run plugin -- pack path/to/plugin`
2. Put the `.tessera-plugin` file in `plugins/` and open a pull request.

That's it. The **Build marketplace** GitHub Action reads each package's `manifest.json` and fills in `marketplace.json` (name, author, version, description, icon, download link and SHA-256) and the plugin table in the README. On a pull request it only checks that the packages are valid; once merged into `main` it commits the updated files.

To ship a new version, add the new package next to the old one. The highest version is listed. Extra fields you add by hand to an entry, like `homepage`, are kept.

Plugins hosted elsewhere (for example on a GitHub release) can still be added to `marketplace.json` by hand with their own `download` and `sha256`. The action leaves those entries alone.

To run it locally: `python scripts/build.py`

## Hosting your own marketplace

Any GitHub repository with a `marketplace.json` at its root works. In Tessera, open **Plugins → Marketplace → Add a marketplace** and enter `owner/repo`, or an https link to any `.json` file in this format.

### Add-to-Tessera button

Put this in your README, replacing `owner/repo` with your repository. Clicking it opens Tessera, which asks before adding the marketplace.

```html
<a href="https://compagesworks.github.io/Tessera-Marketplace/add.html?repo=owner/repo"><img src="https://raw.githubusercontent.com/CompagesWorks/Tessera-Marketplace/main/assets/add-to-tessera.png" alt="Add repo to Marketplace" width="300"></a>
```

The button goes through `add.html` because GitHub removes `tessera://` links from READMEs. The page forwards to `tessera://marketplace/add?repo=owner/repo`, which you can also use directly anywhere custom links are allowed.
