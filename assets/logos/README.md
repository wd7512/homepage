# Logos

Official logos used as 16x16 pixel icons on the website. They are brand marks
used only to identify the organisation or service they represent; all
trademarks belong to their owners.

## The process

1. Put a square-ish PNG of the **official** logo in this folder (rasterise an
   SVG first if needed, e.g. 512px with a transparent background).
2. Add an entry to `logos.json`: `src` (file), `colors` (max palette size),
   and optionally `"ink": true` to map near-black pixels to the theme's ink
   colour so a black mark stays visible in dark mode, or `"fill_holes": "#ffffff"`
   to paint enclosed holes (e.g. the letters in ORCID's mark) so they don't take the page
   background. A logo that is too detailed for automatic downsampling can be
   hand-drawn instead: give its entry `rows` (up to 16 equal-width strings) and
   `palette` and they are used as-is.
3. Run the converter (needs the dev dependency Pillow):

   ```
   uv run python scripts/logos_to_pixels.py --preview /tmp/logos.png
   ```

   It crops to the logo's bounding box, pads to a square, downsamples to 16x16
   with Lanczos, thresholds alpha, and reduces to a small palette. Output goes
   to `src/adapters/outbound/logo_pixels.json`, which the site renderer reads.
   `--preview` writes a contact sheet so you can check the result.
4. Reference the name in a content file with `icon: <name>` (or use it in
   `LINK_ICONS` in `pixel_icons.py`).

Re-run the converter whenever a source logo or `logos.json` changes and commit
both the source and the generated JSON.

## Sources

| Name | Source | Licence / note |
| --- | --- | --- |
| github | Hand-drawn 16x16 trace of the GitHub mark (Simple Icons, CC0, as reference) | Palette uses the theme ink colour |
| orcid | Simple Icons, https://cdn.simpleicons.org/orcid | CC0; ORCID iD mark |
| steam | Simple Icons, https://cdn.simpleicons.org/steam | CC0; Steam logo |
| linkedin | Hand-drawn 16x16 version of the LinkedIn "in" mark (reference: Wikimedia Commons `File:LinkedIn_icon.svg`) | Brand blue `#0077b5` |
| bristol | https://www.bristol.ac.uk (favicon-32x32.png) | University of Bristol official site icon; the 32px favicon downsamples better than the 180px touch icon |
| bath | Hand-drawn 16x16 medallion based on the University of Bath site icon | The 180px icon's opaque dark tile and detailed face do not survive downsampling |
