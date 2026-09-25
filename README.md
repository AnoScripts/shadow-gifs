# Shadow GIFs

Generate animated Minecraft-style button GIFs from any text.

**Use it online:** https://anoscripts.github.io/shadow-gifs/

Type one text per line, hit **Generate GIFs**, download. Runs fully in your browser.

Add Minecraft icons (Mobs, Weapons, Tools, Resources, Food) with the buttons under the text box, or type `:name:` (e.g. `:diamond_sword:`, `:creeper:`). "Icon size" sets how big they are. The icons live in `icons.js`, which `python build_icons.py` regenerates from a local Minecraft install.

A Python version (`mc_button_gif.py`, needs Pillow + a local Minecraft install for the font) is included too:

```
python mc_button_gif.py "Hello World"
```
