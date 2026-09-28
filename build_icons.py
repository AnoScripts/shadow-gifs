"""Cut icons (item textures, mob head faces) from the installed Minecraft jar into icons.js.

usage: python build_icons.py   (rerun after a Minecraft update; writes icons.js next to this file)
Output: window.ICONS = {category: {name: png data url}}. Items are 16px; heads are drawn at 2x so an
8px face matches them. The page scales everything by (icon size / 16).
"""
import base64, glob, io, json, os, zipfile
from PIL import Image

T = "assets/minecraft/textures/"
F8 = (8, 8, 8, 8)  # front face of a standard 8x8x8 head at texOffs(0,0)
# name: (texture, (face x, y, w, h), overlays [(x, y, w, h, dx, dy)] composited onto the face)
HAT = [(40, 8, 8, 8, 0, 0)]  # 64x64 player-layout skins
MOBS = {"steve": ("entity/player/wide/steve", F8, HAT), "alex": ("entity/player/wide/alex", F8, HAT),
        "zombie": ("entity/zombie/zombie", F8, HAT), "husk": ("entity/zombie/husk", F8, HAT),
        "drowned": ("entity/zombie/drowned", F8, HAT), "creeper": ("entity/creeper/creeper", F8, []),
        "skeleton": ("entity/skeleton/skeleton", F8, []), "stray": ("entity/skeleton/stray", F8, []),
        "wither_skeleton": ("entity/skeleton/wither_skeleton", F8, []),
        "enderman": ("entity/enderman/enderman", (8, 24, 8, 8), [(8, 8, 8, 8, 0, 0)]),  # jaw layer + eyes layer
        "blaze": ("entity/blaze/blaze", F8, []),
        "spider": ("entity/spider/spider", (40, 12, 8, 8), []),
        "cave_spider": ("entity/spider/cave_spider", (40, 12, 8, 8), []),
        "piglin": ("entity/piglin/piglin", (8, 8, 10, 8), []),
        "zombified_piglin": ("entity/piglin/zombified_piglin", (8, 8, 10, 8), []),
        "villager": ("entity/villager/villager", (8, 8, 8, 10), []),
        "witch": ("entity/witch/witch", (8, 8, 8, 10), []),
        "iron_golem": ("entity/iron_golem/iron_golem", (8, 8, 8, 10), []),
        "pig": ("entity/pig/pig_temperate", F8, [(17, 17, 4, 3, 2, 4)]),  # + snout
        "ghast": ("entity/ghast/ghast", (32, 32, 32, 32), []),  # 2x-res texture
        "wither": ("entity/wither/wither", F8, []),
        "warden": ("entity/warden/warden", (10, 42, 16, 16), []),
        "bogged": ("entity/skeleton/bogged", F8, []),
        "zombie_villager": ("entity/zombie_villager/zombie_villager", (8, 8, 8, 10), []),
        "piglin_brute": ("entity/piglin/piglin_brute", (8, 8, 10, 8), []),
        "pillager": ("entity/illager/pillager", (8, 8, 8, 10), []),
        "vindicator": ("entity/illager/vindicator", (8, 8, 8, 10), []),
        "evoker": ("entity/illager/evoker", (8, 8, 8, 10), []),
        "wandering_trader": ("entity/wandering_trader/wandering_trader", (8, 8, 8, 10), []),
        "snow_golem": ("entity/snow_golem/snow_golem", F8, []),
        "chicken": ("entity/chicken/chicken_temperate", (3, 3, 4, 6), [(16, 2, 4, 2, 0, 2), (16, 6, 2, 2, 1, 4)]),  # + beak, wattle
        "allay": ("entity/allay/allay", (5, 5, 5, 5), [])}
MOBS.update({n: (f"entity/player/wide/{n}", F8, HAT) for n in ["ari", "efe", "kai", "makena", "noor", "sunny", "zuri"]})
ITEMS = {
    "Weapons": ["wooden_sword", "stone_sword", "iron_sword", "golden_sword", "diamond_sword", "netherite_sword",
                "bow", "crossbow_standby", "arrow", "spectral_arrow", "trident", "mace", "fire_charge", "wind_charge",
                "snowball", "egg", "splash_potion", "turtle_helmet", "diamond_helmet", "diamond_chestplate",
                "netherite_helmet", "netherite_chestplate"],
    "Tools": ["iron_pickaxe", "golden_pickaxe", "diamond_pickaxe", "netherite_pickaxe", "diamond_axe", "netherite_axe",
              "diamond_shovel", "diamond_hoe", "shears", "flint_and_steel", "fishing_rod", "compass_00", "clock_00",
              "spyglass", "bucket", "water_bucket", "lava_bucket", "wooden_pickaxe", "stone_pickaxe", "iron_axe",
              "golden_axe", "iron_shovel", "netherite_shovel", "netherite_hoe", "brush", "lead", "name_tag", "saddle",
              "elytra", "firework_rocket", "recovery_compass_00", "filled_map", "book", "writable_book",
              "enchanted_book", "carrot_on_a_stick", "bundle"],
    "Resources": ["diamond", "emerald", "netherite_ingot", "netherite_scrap", "iron_ingot", "gold_ingot", "copper_ingot",
                  "coal", "redstone", "lapis_lazuli", "quartz", "amethyst_shard", "blaze_rod", "ender_pearl",
                  "nether_star", "totem_of_undying", "experience_bottle", "raw_iron", "raw_gold", "raw_copper",
                  "iron_nugget", "gold_nugget", "echo_shard", "heart_of_the_sea", "nautilus_shell", "prismarine_shard",
                  "prismarine_crystals", "slime_ball", "gunpowder", "bone", "string", "feather", "leather", "ghast_tear",
                  "magma_cream", "phantom_membrane", "shulker_shell", "dragon_breath", "glowstone_dust", "stick",
                  "flint", "clay_ball", "brick", "paper", "ender_eye", "breeze_rod",
                  "netherite_upgrade_smithing_template"],
    "Food": ["apple", "golden_apple", "bread", "cooked_beef", "cooked_porkchop", "cooked_chicken", "carrot",
             "golden_carrot", "baked_potato", "cake", "cookie", "melon_slice", "pumpkin_pie", "sweet_berries",
             "glow_berries", "honey_bottle", "mushroom_stew", "potato", "cooked_mutton", "cooked_rabbit", "cooked_cod",
             "cooked_salmon", "beetroot", "beetroot_soup", "rabbit_stew", "suspicious_stew", "pufferfish",
             "tropical_fish", "chorus_fruit", "dried_kelp", "poisonous_potato", "rotten_flesh", "spider_eye",
             "milk_bucket"],
}
HEARTS = {"heart": "full", "golden_heart": "absorbing_full", "hardcore_heart": "hardcore_full"}


def jar():
    for j in sorted(glob.glob(os.path.expandvars(r"%APPDATA%\.minecraft\versions\*\*.jar")), key=os.path.getmtime, reverse=True):
        z = zipfile.ZipFile(j)
        if T + "item/diamond_sword.png" in z.namelist():
            return z
    raise SystemExit("No Minecraft jar with textures found")


def url(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def main():
    z = jar()
    png = lambda p: Image.open(io.BytesIO(z.read(T + p + ".png"))).convert("RGBA")
    out = {"Mobs": {}}
    for n, (tex, (x, y, w, h), overlays) in MOBS.items():
        img = png(tex)
        face = img.crop((x, y, x + w, y + h))
        for ox, oy, ow, oh, dx, dy in overlays:
            face.alpha_composite(img.crop((ox, oy, ox + ow, oy + oh)), (dx, dy))
        k = 2 if h <= 10 else 16 / h  # 8px face -> 16px; big/hi-res faces down to 16
        out["Mobs"][n] = url(face.resize((round(w * k), round(h * k)), Image.NEAREST))
    for cat, names in ITEMS.items():
        out[cat] = {n.removesuffix("_00").removesuffix("_standby"): url(png("item/" + n)) for n in names}
    # hearts are 9px HUD sprites: 2x -> 18, close enough to 16
    out["Resources"].update({n: url(png("gui/sprites/hud/heart/" + f).resize((18, 18), Image.NEAREST))
                             for n, f in HEARTS.items()})
    # banner: 20x40 front face of every pattern (greyscale, tinted by dye in the page) + the 20x2 top bar
    B = T + "entity/banner/"
    banner = {n[len(B):-4]: url(Image.open(io.BytesIO(z.read(n))).convert("RGBA").crop((1, 1, 21, 41)))
              for n in z.namelist() if n.startswith(B) and n.endswith(".png") and not n.endswith("banner_base.png")}
    banner["bar"] = url(png("entity/banner/banner_base").crop((2, 44, 22, 46)))
    # signs: the GUI edit-screen textures are flat front views (standing 24x26 = board + stick, hanging 16x16 = chains + board)
    G = T + "gui/"
    signs = {k: {n[len(G + d):-4]: url(Image.open(io.BytesIO(z.read(n))).convert("RGBA"))
                 for n in sorted(z.namelist()) if n.startswith(G + d) and n.endswith(".png")}
             for k, d in (("standing", "signs/"), ("hanging", "hanging_signs/"))}
    # fishing: bobber, cast rod (the page draws the line), 16x512 greyscale water strip = 32 frames (tinted in the page)
    fishing = {n: url(png(p)) for n, p in (("hook", "entity/fishing/fishing_hook"), ("rod", "item/fishing_rod_cast"),
                                           ("water", "block/water_still"))}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons.js")
    with open(path, "w") as f:
        f.write("// generated by build_icons.py from the Minecraft jar\nwindow.ICONS = " + json.dumps(out, indent=0) + ";\n"
                "window.BANNER = " + json.dumps(banner, indent=0) + ";\n"
                "window.SIGNS = " + json.dumps(signs, indent=0) + ";\n"
                "window.FISHING = " + json.dumps(fishing, indent=0) + ";\n")
    print(path, {c: len(v) for c, v in out.items()}, "banner:", len(banner))


if __name__ == "__main__":
    main()
