"""Generate the Hillpointe/Alinos -> Dagster CSS variable override.

Dagster applies exactly one theme class to <body>, so each block must carry the
complete token set -- the NoRedGreen variants cannot inherit from their base.
This generator keeps the 6 blocks in sync from one source of truth.

Red/green substitution for the NoRedGreen variants follows Dagster's own intent
(red -> yellow, green -> blue), using the Alinos *-ink tokens wherever the fill
value would fail contrast as text.
"""

# --- Alinos semantic roles, per mode (HSL forms from the token file) ---
LIGHT = {
    "bg0": "hsl(40 34% 96%)",
    "bg1": "hsl(40 40% 97.5%)",
    "bg2": "hsl(42 46% 99%)",
    "bg3": "hsl(0 0% 100%)",
    "text": "hsl(211 28% 15%)",
    "text2": "hsl(211 16% 36%)",
    "text3": "hsl(211 12% 45%)",
    "brand": "hsl(211 74% 45%)",
    "brand_hover": "hsl(211 78% 39%)",
    "brand_2": "hsl(211 72% 36%)",
    "brand_2_ink": "hsl(211 72% 36%)",
    "brand_line": "hsl(211 74% 45% / .42)",
    "line": "hsl(211 26% 18% / .12)",
    "line2": "hsl(211 24% 18% / .2)",
    # Status green/red deviate from Alinos on purpose: its --pos is hue 176
    # (teal) which does not read as "success green". Shifted to a true green,
    # and the red deepened, both re-checked for WCAG AA on --bg-0.
    "pos": "hsl(145 60% 27%)",        # 5.80:1
    "pos_hover": "hsl(145 60% 22%)",
    "neg": "hsl(0 70% 44%)",          # 5.63:1
    "neg_hover": "hsl(0 70% 39%)",
    "warn": "hsl(48 66% 40%)",
    "warn_hover": "hsl(48 64% 43%)",
    "warn_ink": "hsl(48 66% 31%)",
    "scrim": "hsl(211 28% 15% / .35)",
    "shadow": "hsl(211 28% 28% / .16)",
    "nav_bg": "hsl(211 67% 4%)",
    "tooltip_bg": "hsl(211 28% 15%)",
    "tooltip_text": "hsl(40 34% 96%)",
    "disabled_bg": "hsl(211 26% 18% / .08)",
    "soft": ".1",
    "soft_hover": ".15",
    # Chart fills: the Alinos light-mode --pos / --neg tokens, so charts match
    # the brand palette rather than the shifted status accents above.
    "viz_green": "hsl(176 50% 32%)",
    "viz_red": "hsl(0 64% 46%)",
    "viz_yellow": "hsl(42 85% 52%)",
}

DARK = {
    "bg0": "hsl(211 67% 4%)",
    "bg1": "hsl(211 65% 7%)",
    "bg2": "hsl(211 63% 12%)",
    "bg3": "hsl(211 59% 17%)",
    "text": "hsl(41 42% 93%)",
    "text2": "hsl(211 34% 71%)",
    "text3": "hsl(211 21% 58%)",
    "brand": "hsl(211 87% 69%)",
    "brand_hover": "hsl(211 94% 74%)",
    "brand_2": "hsl(211 60% 45%)",
    "brand_2_ink": "hsl(211 60% 59%)",
    "brand_line": "hsl(211 87% 69% / .5)",
    "line": "hsl(41 42% 93% / .08)",
    "line2": "hsl(41 42% 93% / .15)",
    # See the light-mode note: true green instead of Alinos teal, red made
    # less pink. Both clear AA against --bg-0 and the --bg-2 panel surface.
    "pos": "hsl(145 65% 62%)",        # 11.6:1 on bg-0, 9.8:1 on bg-2
    "pos_hover": "hsl(145 65% 68%)",
    "neg": "hsl(0 85% 68%)",          # 6.6:1 on bg-0, 5.6:1 on bg-2
    "neg_hover": "hsl(0 85% 74%)",
    "warn": "hsl(48 46% 61%)",
    "warn_hover": "hsl(48 82% 61%)",
    "warn_ink": "hsl(48 46% 61%)",
    "scrim": "hsl(0 0% 0% / .55)",
    "shadow": "hsl(0 0% 0% / .5)",
    "nav_bg": "hsl(211 65% 7%)",
    "tooltip_bg": "hsl(211 59% 17%)",
    "tooltip_text": "hsl(41 42% 93%)",
    "disabled_bg": "hsl(41 42% 93% / .08)",
    "soft": ".12",
    "soft_hover": ".18",
    # Chart fills match the accents; they are already bright on dark surfaces.
    "viz_green": None,
    "viz_red": None,
    "viz_yellow": None,
}

# "Custom theme 1" -- an alternate dark theme (user-selectable, not the default):
# warm stone greys, amber accent, green success, red failure, gold warnings.
CUSTOM_1 = {
    "bg0": "hsl(30 10% 8%)",
    "bg1": "hsl(30 9% 11%)",
    "bg2": "hsl(30 8% 15%)",
    "bg3": "hsl(30 8% 20%)",
    "text": "hsl(40 30% 90%)",
    "text2": "hsl(35 15% 72%)",
    "text3": "hsl(35 10% 58%)",
    "brand": "hsl(35 95% 58%)",
    "brand_hover": "hsl(38 100% 66%)",
    "brand_2": "hsl(25 85% 45%)",
    "brand_2_ink": "hsl(30 90% 62%)",
    "brand_line": "hsl(35 95% 58% / .5)",
    "line": "hsl(40 30% 90% / .1)",
    "line2": "hsl(40 30% 90% / .18)",
    "pos": "hsl(145 70% 50%)",
    "pos_hover": "hsl(145 70% 58%)",
    "neg": "hsl(0 85% 62%)",
    "neg_hover": "hsl(0 85% 69%)",
    "warn": "hsl(48 95% 55%)",
    "warn_hover": "hsl(48 100% 62%)",
    "warn_ink": "hsl(48 95% 55%)",
    "scrim": "hsl(0 0% 0% / .6)",
    "shadow": "hsl(0 0% 0% / .6)",
    "nav_bg": "hsl(30 10% 6%)",
    "tooltip_bg": "hsl(30 8% 20%)",
    "tooltip_text": "hsl(40 30% 90%)",
    "disabled_bg": "hsl(40 30% 90% / .08)",
    "soft": ".14",
    "soft_hover": ".2",
    # Chart fills match the accents; they are already bright on dark surfaces.
    "viz_green": None,
    "viz_red": None,
    "viz_yellow": None,
}

# Extras that only apply to Custom theme 1.
CUSTOM_1_EXTRAS = """
.themeCustom1 {
  --font-default: Geist Mono, Roboto Mono, Menlo, monospace;
}

/* Square everything off for a blocky look. */
.themeCustom1 *,
.themeCustom1 *::before,
.themeCustom1 *::after {
  border-radius: 0 !important;
}
"""

# "Alinos light" / "Alinos dark" -- the Alinos token file verbatim, including
# its teal --pos and its --neg, with no status-colour shifts. Chart fills follow
# --pos / --neg too.
ALINOS_LIGHT = {
    **LIGHT,
    "pos": "hsl(176 50% 32%)",
    "pos_hover": "hsl(176 50% 27%)",
    "neg": "hsl(0 64% 46%)",
    "neg_hover": "hsl(0 64% 41%)",
    "viz_green": None,
    "viz_red": None,
    "viz_yellow": None,
}

ALINOS_DARK = {
    **DARK,
    "pos": "hsl(176 68% 70%)",
    "pos_hover": "hsl(176 68% 76%)",
    "neg": "hsl(0 100% 74%)",
    "neg_hover": "hsl(0 100% 80%)",
}

# "Halloween" -- midnight purple page, witch-purple sidebar, pumpkin orange
# accent, slime green success and blood red failure.
HALLOWEEN = {
    "bg0": "hsl(268 40% 7%)",
    "bg1": "hsl(268 38% 10%)",
    "bg2": "hsl(268 36% 14%)",
    "bg3": "hsl(268 34% 19%)",
    "text": "hsl(40 30% 93%)",
    "text2": "hsl(270 30% 78%)",
    "text3": "hsl(270 20% 62%)",
    "brand": "hsl(25 100% 56%)",
    "brand_hover": "hsl(28 100% 64%)",
    "brand_2": "hsl(275 70% 45%)",
    "brand_2_ink": "hsl(275 80% 72%)",
    "brand_line": "hsl(25 100% 56% / .6)",
    "line": "hsl(270 40% 80% / .14)",
    "line2": "hsl(270 40% 80% / .26)",
    "pos": "hsl(100 85% 55%)",
    "pos_hover": "hsl(100 90% 63%)",
    "neg": "hsl(355 90% 58%)",
    "neg_hover": "hsl(355 90% 66%)",
    "warn": "hsl(45 100% 60%)",
    "warn_hover": "hsl(45 100% 68%)",
    "warn_ink": "hsl(45 100% 60%)",
    "scrim": "hsl(268 50% 3% / .75)",
    "shadow": "hsl(25 100% 50% / .25)",
    "nav_bg": "hsl(272 55% 20%)",
    "tooltip_bg": "hsl(272 55% 20%)",
    "tooltip_text": "hsl(40 30% 93%)",
    "disabled_bg": "hsl(270 40% 80% / .1)",
    "soft": ".2",
    "soft_hover": ".3",
    "viz_green": None,
    "viz_red": None,
    "viz_yellow": None,
}


def team_extras(cls, nav_bg, stripe):
    """Themes with a solid-colour sidebar, so every token the nav uses is
    re-pointed inside it (white text, white washes for hover and selection),
    plus a trim stripe along the top of the page."""
    return f"""
.{cls} .hp-nav {{
  background: {nav_bg};
  box-shadow: inset -1px 0 0 hsl(0 0% 100% / 0.25);
  --color-text-default: hsl(0 0% 100%);
  --color-text-light: hsl(0 0% 100% / 0.9);
  --color-text-lighter: hsl(0 0% 100% / 0.78);
  --color-accent-gray: hsl(0 0% 100% / 0.78);
  --color-accent-primary: hsl(0 0% 100%);
  --color-accent-blue: hsl(0 0% 100%);
  --color-link-default: hsl(0 0% 100%);
  --color-link-hover: hsl(0 0% 100%);
  --color-background-light: hsl(0 0% 100% / 0.1);
  --color-background-lighter: hsl(0 0% 100% / 0.12);
  --color-background-lighter-hover: hsl(0 0% 100% / 0.18);
  --color-background-blue: hsl(0 0% 100% / 0.22);
  --color-background-blue-hover: hsl(0 0% 100% / 0.3);
  --color-keyline-default: hsl(0 0% 100% / 0.18);
  --color-border-default: hsl(0 0% 100% / 0.18);
  --color-focus-ring: hsl(0 0% 100% / 0.6);
}}

.{cls} .hp-main {{
  box-shadow: inset 0 4px 0 {stripe};
}}
"""


# A pumpkin glow rising from the bottom of the sidebar.
HALLOWEEN_EXTRAS = team_extras(
    "themeHalloween",
    "linear-gradient(180deg, hsl(272 55% 20%) 55%, hsl(25 90% 32%) 100%)",
    "hsl(25 100% 56%)",
)

# Halloween only: a cobweb in the top-right corner and a spider swinging on a
# thread. Both fixed to the viewport and click-through.
HALLOWEEN_DECOR = """
.themeHalloween .hp-main::before,
.themeHalloween .hp-main::after {
  content: '';
  position: fixed;
  pointer-events: none;
  z-index: 5;
  background-repeat: no-repeat;
  background-size: contain;
}

.themeHalloween .hp-main::before {
  top: 4px;
  right: 0;
  width: 110px;
  height: 110px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200' fill='none' stroke='white' stroke-opacity='0.55' stroke-width='1.2'%3E %3Cpath d='M200 0 L0 0 M200 0 L0 40 M200 0 L0 110 M200 0 L30 200 M200 0 L110 200 M200 0 L200 200'/%3E %3Cpath d='M160 0 Q150 25 170 40 Q190 55 200 40'/%3E %3Cpath d='M120 0 Q105 45 140 80 Q175 110 200 80'/%3E %3Cpath d='M80 0 Q60 70 110 120 Q160 165 200 120'/%3E %3Cpath d='M40 0 Q15 95 80 160 Q145 220 200 160'/%3E %3C/svg%3E");
}

.themeHalloween .hp-main::after {
  top: 4px;
  right: 150px;
  width: 32px;
  height: 110px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 200'%3E %3Cline x1='30' y1='0' x2='30' y2='150' stroke='white' stroke-opacity='0.6' stroke-width='1'/%3E %3Cg stroke='%23111' stroke-width='2.5' stroke-linecap='round' fill='none'%3E %3Cpath d='M24 158 L8 146 L2 134 M24 162 L6 160 M24 166 L8 176 L2 186 M26 170 L14 186'/%3E %3Cpath d='M36 158 L52 146 L58 134 M36 162 L54 160 M36 166 L52 176 L58 186 M34 170 L46 186'/%3E %3C/g%3E %3Ccircle cx='30' cy='154' r='5' fill='%23111'/%3E %3Cellipse cx='30' cy='168' rx='9' ry='11' fill='%23111'/%3E %3Ccircle cx='28' cy='152' r='1.2' fill='%23ff5a1f'/%3E%3Ccircle cx='32' cy='152' r='1.2' fill='%23ff5a1f'/%3E %3C/svg%3E");
  transform-origin: top center;
  animation: hpSpiderSwing 4s ease-in-out infinite;
}

@keyframes hpSpiderSwing {
  0%, 100% { transform: rotate(-6deg) translateY(0); }
  50% { transform: rotate(6deg) translateY(10px); }
}
"""

# hue-only forms, for building translucent fills
HUE = {
    "light": {"pos": "145 60% 27%", "neg": "0 70% 44%", "warn": "48 66% 40%",
              "brand": "211 74% 45%", "brand_2": "211 72% 36%", "gray": "211 26% 18%"},
    "dark": {"pos": "145 65% 62%", "neg": "0 85% 68%", "warn": "48 46% 61%",
             "brand": "211 87% 69%", "brand_2": "211 60% 45%", "gray": "41 42% 93%"},
    "alinos_light": {"pos": "176 50% 32%", "neg": "0 64% 46%", "warn": "48 66% 40%",
                     "brand": "211 74% 45%", "brand_2": "211 72% 36%", "gray": "211 26% 18%"},
    "alinos_dark": {"pos": "176 68% 70%", "neg": "0 100% 74%", "warn": "48 46% 61%",
                    "brand": "211 87% 69%", "brand_2": "211 60% 45%", "gray": "41 42% 93%"},
    "custom1": {"pos": "145 70% 50%", "neg": "0 85% 62%", "warn": "48 95% 55%",
                 "brand": "35 95% 58%", "brand_2": "25 85% 45%", "gray": "40 30% 90%"},
    "halloween": {"pos": "100 85% 55%", "neg": "355 90% 58%", "warn": "45 100% 60%",
                  "brand": "25 100% 56%", "brand_2": "275 70% 45%", "gray": "270 40% 80%"},
}


def block(m, mode, hue=None):
    """Emit the full token set for one theme block.

    Dagster ships NoRedGreen theme variants that swap red->yellow and
    green->blue for red-green colorblindness. We deliberately do NOT do that
    substitution: failure is always red and success is always green in every
    variant, so the NoRedGreen classes render identically to their base.
    """
    h = HUE[hue or mode]
    a = m["soft"]
    ah = m["soft_hover"]

    green_fill, green_hover, green_text, green_hue = (
        m["pos"], m["pos_hover"], m["pos"], h["pos"])
    red_fill, red_hover, red_text, red_hue = (
        m["neg"], m["neg_hover"], m["neg"], h["neg"])

    return f"""  --browser-color-scheme: {mode};

  --color-background-default: {m['bg0']};
  --color-background-default-hover: {m['bg1']};
  --color-background-light: {m['bg1']};
  --color-background-light-hover: {m['bg2']};
  --color-background-lighter: {m['bg2']};
  --color-background-lighter-hover: {m['bg3']};
  --color-background-disabled: {m['disabled_bg']};

  --color-text-default: {m['text']};
  --color-text-light: {m['text2']};
  --color-text-lighter: {m['text3']};
  --color-text-disabled: {m['text3']};

  --color-accent-primary: {m['brand']};
  --color-accent-primary-hover: {m['brand_hover']};
  --color-accent-blue: {m['brand']};
  --color-accent-blue-hover: {m['brand_hover']};
  --color-accent-reversed: {m['bg0']};
  --color-accent-reversed-hover: {m['bg1']};
  --color-accent-gray: {m['text3']};
  --color-accent-gray-hover: {m['text2']};
  --color-link-default: {m['brand']};
  --color-link-hover: {m['brand_hover']};
  --color-link-disabled: {m['text3']};
  --color-text-blue: {m['brand']};
  --color-focus-ring: {m['brand_line']};
  --color-checkbox-checked: {m['brand']};
  --color-checkbox-unchecked: {m['text3']};
  --color-checkbox-disabled: {m['text3']};

  --color-border-default: {m['line']};
  --color-border-hover: {m['line2']};
  --color-border-disabled: {m['line']};
  --color-keyline-default: {m['line']};

  --color-accent-green: {green_fill};
  --color-accent-green-hover: {green_hover};
  --color-accent-red: {red_fill};
  --color-accent-red-hover: {red_hover};
  --color-accent-yellow: {m['warn']};
  --color-accent-yellow-hover: {m['warn_hover']};
  --color-text-green: {green_text};
  --color-text-red: {red_text};
  --color-text-yellow: {m['warn_ink']};
  --color-background-green: hsl({green_hue} / {a});
  --color-background-green-hover: hsl({green_hue} / {ah});
  --color-background-red: hsl({red_hue} / {a});
  --color-background-red-hover: hsl({red_hue} / {ah});
  --color-background-yellow: hsl({h['warn']} / {a});
  --color-background-yellow-hover: hsl({h['warn']} / {ah});
  --color-background-blue: hsl({h['brand']} / {a});
  --color-background-blue-hover: hsl({h['brand']} / {ah});
  --color-background-gray: hsl({h['gray']} / {a});
  --color-background-gray-hover: hsl({h['gray']} / {ah});

  --color-nav-background: {m['nav_bg']};
  --color-nav-text: {m['text2']};
  --color-nav-text-hover: {m['text']};
  --color-nav-text-selected: {m['text']};
  --color-nav-button: {m['bg2']};
  --color-nav-button-hover: {m['bg3']};

  --color-popover-background: {m['bg2']};
  --color-popover-background-hover: {m['bg3']};
  --color-dialog-background: {m['scrim']};
  --color-tooltip-background: {m['tooltip_bg']};
  --color-tooltip-text: {m['tooltip_text']};
  --color-shadow-default: {m['shadow']};

  --color-lineage-edge: {m['line2']};
  --color-lineage-edge-highlighted: {m['brand']};
  --color-lineage-node-background: {m['bg2']};
  --color-lineage-node-background-hover: {m['bg3']};
  --color-lineage-node-border: {m['line']};
  --color-lineage-node-border-hover: {m['line2']};
  --color-lineage-node-border-selected: {m['brand']};
  --color-lineage-group-node-background: {m['bg1']};
  --color-lineage-group-node-background-hover: {m['bg2']};
  --color-lineage-group-node-border: {m['line']};
  --color-lineage-group-node-border-hover: {m['line2']};

  --color-data-viz-green: {m['viz_green'] or green_fill};
  --color-data-viz-green-alt: {green_hover};
  --color-data-viz-red: {m['viz_red'] or red_fill};
  --color-data-viz-red-alt: {red_hover};
  --color-data-viz-blue: {m['brand']};
  --color-data-viz-blue-alt: {m['brand_2']};
  --color-data-viz-yellow: {m['viz_yellow'] or m['warn']};
  --color-data-viz-yellow-alt: {m['warn_hover']};
  --color-data-viz-gray: {m['text3']};
  --color-data-viz-gray-alt: {m['text2']};
"""


HEADER = """/* ============================================================================
 * Hillpointe theme -- Alinos design tokens mapped onto Dagster's --color-*
 * system.
 *
 * GENERATED -- do not hand-edit. Regenerate with:
 *   python gen_hillpointe_theme.py > HillpointeTheme.css
 *
 * Imported from src/css/theme.css AFTER GlobalThemeStyle.css so these win the
 * cascade. GlobalThemeStyle.css itself is left as upstream ships it, so the
 * fork can rebase onto new Dagster versions without conflicts here.
 *
 * Dagster sets exactly one theme class on <body>, so every block carries the
 * complete token set. Source order puts the explicit .theme* classes after the
 * prefers-color-scheme queries so an explicit choice beats the OS preference.
 *
 * Failure is red and success is green in every variant, including the
 * NoRedGreen ones -- Dagster's red->yellow / green->blue colorblind swap is
 * intentionally not carried over.
 * ========================================================================== */
"""


def main():
    out = [HEADER]

    out.append("@media (prefers-color-scheme: light) {")
    out.append("  :root, .themeSystem, .themeSystemNoRedGreen {\n"
               + block(LIGHT, "light") + "  }")
    out.append("}\n")

    out.append("@media (prefers-color-scheme: dark) {")
    out.append("  :root, .themeSystem, .themeSystemNoRedGreen {\n"
               + block(DARK, "dark") + "  }")
    out.append("}\n")

    out.append(".themeLight, .themeLightNoRedGreen {\n" + block(LIGHT, "light") + "}\n")
    out.append(".themeDark, .themeDarkNoRedGreen {\n" + block(DARK, "dark") + "}\n")
    out.append(".themeCustom1 {\n" + block(CUSTOM_1, "dark", "custom1") + "}\n")
    out.append(".themeAlinosLight {\n" + block(ALINOS_LIGHT, "light", "alinos_light") + "}\n")
    out.append(".themeAlinosDark {\n" + block(ALINOS_DARK, "dark", "alinos_dark") + "}\n")
    out.append(CUSTOM_1_EXTRAS)
    out.append(".themeHalloween {\n" + block(HALLOWEEN, "dark", "halloween") + "}\n")
    out.append(HALLOWEEN_EXTRAS)
    out.append(HALLOWEEN_DECOR)

    return "\n".join(out)


if __name__ == "__main__":
    import sys
    sys.stdout.write(main())
