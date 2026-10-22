"""Design tokens -> CSS. tokens.json is the single source of truth.

`python -m truesum.ui.theme` regenerates replica/design/tokens.css.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

TOKENS_PATH = Path(__file__).resolve().parents[2] / "replica" / "design" / "tokens.json"


@lru_cache(maxsize=1)
def tokens() -> dict:
    return json.loads(TOKENS_PATH.read_text())


def color(role: str) -> str:
    return tokens()["color"][role]


def chart_colors() -> list[str]:
    return tokens()["chart"]["categorical"]


def css_variables() -> str:
    t = tokens()
    lines = [f"  --color-{k}: {v};" for k, v in t["color"].items()]
    lines += [f"  --font-{k}: {v};" for k, v in t["font"].items()]
    for name, spec in t["type"].items():
        lines.append(f"  --text-{name}: {spec['size']}px;")
        lines.append(f"  --leading-{name}: {spec['line']}px;")
        lines.append(f"  --weight-{name}: {spec['weight']};")
    lines += [f"  --space-{i}: {v}px;" for i, v in enumerate(t["space"])]
    lines += [f"  --radius-{k}: {v}px;" for k, v in t["radius"].items()]
    lines += [f"  --shadow-{k}: {v};" for k, v in t["shadow"].items()]
    lines += [f"  --motion-{k}: {v};" for k, v in t["motion"].items()]
    lines += [f"  --layout-{k}: {v}px;" for k, v in t["layout"].items()]
    return ":root {\n" + "\n".join(lines) + "\n}\n"


COMPONENT_CSS = """
/* layout */
.block-container { max-width: var(--layout-content-max); padding-top: var(--space-5); }

/* focus: visible on every interactive element */
:is(button, [role="button"], input, select, textarea, a, [tabindex]):focus-visible {
  outline: 2px solid var(--color-focus-ring) !important;
  outline-offset: 2px;
}

/* primary buttons: Streamlit draws light text on the accent (~2:1); use on-accent (9.1:1) */
button[kind="primary"], button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  color: var(--color-on-accent) !important;
}
button[kind="primary"] *, button[kind="primaryFormSubmit"] *,
[data-testid="stBaseButton-primary"] *, [data-testid="stBaseButton-primaryFormSubmit"] * {
  color: var(--color-on-accent) !important;
}

/* section headings are h2 (st.header) but sized like subheadings */
[data-testid="stHeading"] h2 { font-size: var(--text-lg); line-height: var(--leading-lg); padding-top: var(--space-4); }

/* page header */
.sl-hero {
  background: linear-gradient(135deg, var(--color-hero-from), var(--color-hero-via), var(--color-hero-to));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-6);
  margin-bottom: var(--space-5);
  display: flex; align-items: center; gap: var(--space-4);
}
.sl-hero img { width: 56px; height: 56px; border-radius: var(--radius-md); box-shadow: var(--shadow-md); }
.sl-hero h1 {
  margin: 0; padding: 0;
  font-size: var(--text-xl); line-height: var(--leading-xl); font-weight: var(--weight-hero);
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent-2));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.sl-hero p { margin: var(--space-1) 0 0; color: var(--color-text); font-size: var(--text-sm); }

/* metric card */
.sl-metric {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--space-4);
  margin-bottom: var(--space-3);
}
.sl-metric .label { color: var(--color-text-muted); font-size: var(--text-xs); font-weight: var(--weight-xs);
  text-transform: uppercase; letter-spacing: .04em; }
.sl-metric-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-3);
  margin-bottom: var(--space-3); }
.sl-metric-row .sl-metric { margin-bottom: 0; }
/* numbers never break mid-number; the grid wraps cards before they get too narrow */
.sl-metric .value { color: var(--color-text); font-size: var(--text-metric); line-height: var(--leading-metric);
  font-weight: var(--weight-metric); font-variant-numeric: tabular-nums; margin-top: var(--space-1); white-space: nowrap; }
.sl-metric .hint { color: var(--color-text-muted); font-size: var(--text-xs); margin-top: var(--space-1); }

/* tier badge: colour + text + shape, never colour alone */
.sl-badge {
  display: inline-flex; align-items: center; gap: var(--space-1);
  padding: 2px var(--space-2); border-radius: 999px; font-size: var(--text-xs); font-weight: 600;
  border: 1px solid currentColor; background: var(--color-surface);
}
.sl-badge.high { color: var(--color-tier-high); }
.sl-badge.medium { color: var(--color-tier-medium); }
.sl-badge.low { color: var(--color-tier-low); }

/* empty state */
.sl-empty {
  border: 1px dashed var(--color-border-input); border-radius: var(--radius-lg);
  padding: var(--space-7) var(--space-5); text-align: center; background: var(--color-surface);
}
.sl-empty h3 { margin: 0 0 var(--space-2); font-size: var(--text-lg); color: var(--color-text); }
.sl-empty p { margin: 0; color: var(--color-text-muted); font-size: var(--text-sm); }

/* step list (audit log) */
.sl-steps { list-style: none; padding: 0; margin: 0; }
.sl-steps li { padding: var(--space-2) 0; border-bottom: 1px solid var(--color-border);
  font-size: var(--text-sm); color: var(--color-text); }
.sl-steps li .meta { color: var(--color-text-muted); font-size: var(--text-xs); margin-left: var(--space-2);
  font-variant-numeric: tabular-nums; }

@media (max-width: 640px) {
  [data-testid="stHeading"] h1 { font-size: var(--text-xl); line-height: var(--leading-xl); }
  .sl-hero { padding: var(--space-4); }
  .sl-hero img { width: 40px; height: 40px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
"""


def full_css() -> str:
    return css_variables() + COMPONENT_CSS


if __name__ == "__main__":
    out = TOKENS_PATH.with_name("tokens.css")
    out.write_text(full_css())
    print(f"wrote {out}")
