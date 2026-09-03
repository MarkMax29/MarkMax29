#!/usr/bin/env python3
"""Generate an animated, dark-blue retro platformer SVG from GitHub contributions.

Designed for the MarkMax29 profile README. The script queries GitHub's GraphQL API
using GITHUB_TOKEN, turns the contribution calendar into a 53x7 pixel-style grid,
and overlays an original side-scrolling runner animation.
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

GITHUB_API = "https://api.github.com/graphql"
USER = os.getenv("GITHUB_USER", "MarkMax29")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTPUT = Path(os.getenv("OUTPUT_SVG", "assets/contribution-run.svg"))

SVG_W = 930
SVG_H = 315
GRID_X = 94
GRID_Y = 82
CELL = 10
GAP = 4
STEP = CELL + GAP
TRACK_Y = 234
DURATION = 12

# Dark-blue palette, tuned to GitHub dark.
BG = "#0D1117"
PANEL = "#0B1623"
GRID_0 = "#162234"
GRID_1 = "#103B66"
GRID_2 = "#0A66C2"
GRID_3 = "#2388E8"
GRID_4 = "#58A6FF"
CYAN = "#79C0FF"
CYAN_2 = "#A5D6FF"
BLUE = "#1F6FEB"
BLUE_DARK = "#0A2D4D"
WHITE = "#F0F6FC"
MUTED = "#8B949E"
GOLD = "#F2C94C"
GOLD_LIGHT = "#FFE082"
GROUND = "#18324A"
GROUND_EDGE = "#58A6FF"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class Day:
    week: int
    weekday: int
    count: int
    date: str


def graphql_request() -> dict:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")

    payload = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode("utf-8")
    req = urllib.request.Request(
        GITHUB_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "MarkMax29-contribution-run",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc

    if data.get("errors"):
        raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")

    return data


def parse_days(data: dict) -> tuple[list[Day], int]:
    user = data.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {USER!r} was not found")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    days: list[Day] = []
    for wi, week in enumerate(weeks):
        for d in week["contributionDays"]:
            days.append(
                Day(
                    week=wi,
                    weekday=int(d["weekday"]),
                    count=int(d["contributionCount"]),
                    date=str(d["date"]),
                )
            )
    return days, int(calendar["totalContributions"])


def level(count: int) -> int:
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 7:
        return 3
    return 4


def svg_rect(x: float, y: float, w: float, h: float, fill: str, rx: float = 2, **attrs: str) -> str:
    extra = " ".join(f'{k.replace("_", "-")}="{escape(str(v))}"' for k, v in attrs.items())
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'


def pixel_runner() -> str:
    """Original pixel runner; intentionally not copied from any game sprite."""
    parts = [
        # cap / head
        svg_rect(4, 0, 14, 3, CYAN, 0),
        svg_rect(1, 3, 17, 3, BLUE, 0),
        svg_rect(5, 6, 10, 7, "#D8B08C", 0),
        svg_rect(12, 8, 2, 2, BG, 0),
        # torso
        svg_rect(4, 13, 12, 9, BLUE, 0),
        svg_rect(7, 14, 6, 5, CYAN_2, 0),
        # arm
        svg_rect(16, 14, 4, 4, "#D8B08C", 0),
        # legs are animated children
        '<g transform="translate(5 22)">'
        + svg_rect(0, 0, 4, 8, CYAN, 0)
        + '<animateTransform attributeName="transform" type="rotate" values="-18 2 0;18 2 0;-18 2 0" dur="0.38s" repeatCount="indefinite"/>'
        + '</g>',
        '<g transform="translate(12 22)">'
        + svg_rect(0, 0, 4, 8, BLUE, 0)
        + '<animateTransform attributeName="transform" type="rotate" values="18 2 0;-18 2 0;18 2 0" dur="0.38s" repeatCount="indefinite"/>'
        + '</g>',
        svg_rect(3, 29, 7, 3, WHITE, 0),
        svg_rect(11, 29, 7, 3, WHITE, 0),
    ]
    return "".join(parts)


def coin(x: int, y: int, disappear_at: float) -> str:
    # Four opacity phases: visible, collect flash, hidden, reset.
    t1 = max(0.0, disappear_at - 0.015)
    t2 = min(0.98, disappear_at + 0.015)
    key_times = f"0;{t1:.3f};{disappear_at:.3f};{t2:.3f};0.98;1"
    return f"""
<g transform="translate({x} {y})">
  <rect x="2" y="0" width="8" height="2" fill="{GOLD_LIGHT}"/>
  <rect x="0" y="2" width="12" height="12" rx="3" fill="{GOLD}"/>
  <rect x="4" y="4" width="4" height="8" fill="{GOLD_LIGHT}"/>
  <animate attributeName="opacity" values="1;1;0.35;0;0;1" keyTimes="{key_times}" dur="{DURATION}s" repeatCount="indefinite"/>
  <animateTransform attributeName="transform" additive="sum" type="scale" values="1 1;0.7 1;1 1" dur="0.6s" repeatCount="indefinite"/>
</g>
"""


def bounce_block(x: int, y: int, hit_at: float) -> str:
    before = max(0.0, hit_at - 0.02)
    after = min(0.99, hit_at + 0.04)
    kt = f"0;{before:.3f};{hit_at:.3f};{after:.3f};1"
    return f"""
<g transform="translate({x} {y})">
  <rect x="0" y="0" width="28" height="28" rx="3" fill="{BLUE_DARK}" stroke="{CYAN}" stroke-width="1.5"/>
  <rect x="5" y="5" width="18" height="18" rx="2" fill="{BLUE}" opacity="0.55"/>
  <text x="14" y="20" text-anchor="middle" font-family="monospace" font-size="15" font-weight="700" fill="{WHITE}">?</text>
  <animateTransform attributeName="transform" additive="sum" type="translate" values="0 0;0 0;0 -8;0 0;0 0" keyTimes="{kt}" dur="{DURATION}s" repeatCount="indefinite"/>
</g>
"""


def build_svg(days: Iterable[Day], total: int) -> str:
    days = list(days)
    max_week = max((d.week for d in days), default=52)
    cols = max_week + 1
    # Center grid, but cap to normal GitHub calendar width.
    grid_width = cols * STEP - GAP
    grid_x = max(62, (SVG_W - grid_width) // 2)

    colors = [GRID_0, GRID_1, GRID_2, GRID_3, GRID_4]
    cells: list[str] = []
    for d in days:
        x = grid_x + d.week * STEP
        y = GRID_Y + d.weekday * STEP
        c = colors[level(d.count)]
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}">'
            f'<title>{escape(d.date)}: {d.count} contribution{"s" if d.count != 1 else ""}</title>'
            '</rect>'
        )

    # Pick three strong contribution columns as coin x-positions, but keep reasonable spacing.
    week_scores: dict[int, int] = {}
    for d in days:
        week_scores[d.week] = week_scores.get(d.week, 0) + d.count
    ranked = sorted(week_scores, key=lambda w: (-week_scores[w], w))
    chosen: list[int] = []
    for w in ranked:
        if all(abs(w - prev) >= 8 for prev in chosen):
            chosen.append(w)
        if len(chosen) == 3:
            break
    defaults = [14, 29, 42]
    while len(chosen) < 3:
        candidate = defaults[len(chosen)]
        if candidate <= max_week:
            chosen.append(candidate)
        else:
            chosen.append(max(0, max_week - (2 - len(chosen)) * 10))
    chosen.sort()
    coin_xs = [int(grid_x + w * STEP + CELL / 2 - 6) for w in chosen]

    # Runner follows two jumps, aligned approximately with the middle and last coin.
    start_x = 38
    finish_x = SVG_W - 108
    jump1 = max(220, min(coin_xs[0] - start_x, 320))
    jump2 = max(jump1 + 170, min(coin_xs[1] - start_x, 560))
    end_rel = finish_x - start_x
    path = (
        f"M 0 0 H {jump1 - 38} "
        f"Q {jump1 - 15} -62 {jump1 + 12} -62 "
        f"Q {jump1 + 40} -62 {jump1 + 62} 0 "
        f"H {jump2 - 40} "
        f"Q {jump2 - 15} -48 {jump2 + 10} -48 "
        f"Q {jump2 + 35} -48 {jump2 + 58} 0 "
        f"H {end_rel}"
    )

    # Timings roughly follow horizontal position through the 12s loop.
    def norm_time(x: int) -> float:
        return min(0.88, max(0.10, 0.08 + 0.80 * ((x - start_x) / max(1, finish_x - start_x))))

    coin_timings = [norm_time(x) for x in coin_xs]
    block1_x = int(start_x + jump1 + 22)
    block2_x = int(start_x + jump2 + 20)
    block1_t = norm_time(block1_x)
    block2_t = norm_time(block2_x)

    # Fake small platform bricks across the bottom.
    ground_bricks = []
    for x in range(28, SVG_W - 28, 28):
        fill = GROUND if (x // 28) % 2 == 0 else "#14304A"
        ground_bricks.append(svg_rect(x, TRACK_Y + 32, 26, 17, fill, 2))
    ground = "".join(ground_bricks)

    flag_x = SVG_W - 60
    complete_anim = (
        f'<animate attributeName="opacity" values="0;0;1;1;0" '
        f'keyTimes="0;0.86;0.90;0.97;1" dur="{DURATION}s" repeatCount="indefinite"/>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}" role="img" aria-labelledby="title desc">
<title id="title">Mark's Contribution Run</title>
<desc id="desc">Animated dark-blue retro platformer generated from MarkMax29's GitHub contribution calendar.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{BG}"/>
    <stop offset="100%" stop-color="#071B2E"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2.3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<rect width="{SVG_W}" height="{SVG_H}" rx="18" fill="url(#bg)"/>
<rect x="18" y="18" width="{SVG_W-36}" height="{SVG_H-36}" rx="14" fill="none" stroke="#1D3B57"/>

<text x="42" y="49" font-family="monospace" font-size="18" font-weight="700" fill="{CYAN_2}">MARK'S CONTRIBUTION RUN</text>
<text x="{SVG_W-42}" y="49" text-anchor="end" font-family="monospace" font-size="12" fill="{MUTED}">LEVEL 01  •  {total} CONTRIBUTIONS</text>

<g id="contribution-grid">{''.join(cells)}</g>

<!-- subtle skyline / stars -->
<g opacity="0.35" fill="{CYAN}">
  <circle cx="60" cy="68" r="1.2"/><circle cx="855" cy="70" r="1.1"/><circle cx="803" cy="184" r="1.2"/>
  <circle cx="74" cy="190" r="0.9"/><circle cx="870" cy="165" r="0.8"/>
</g>

<!-- Coins -->
{coin(coin_xs[0], TRACK_Y - 54, coin_timings[0])}
{coin(coin_xs[1], TRACK_Y - 74, coin_timings[1])}
{coin(coin_xs[2], TRACK_Y - 50, coin_timings[2])}

<!-- Retro blocks -->
{bounce_block(block1_x, TRACK_Y - 64, block1_t)}
{bounce_block(block2_x, TRACK_Y - 60, block2_t)}

<!-- Finish flag -->
<g transform="translate({flag_x} {TRACK_Y-68})">
  <rect x="4" y="0" width="3" height="97" fill="{CYAN_2}"/>
  <path d="M7 5 H38 L29 18 L38 31 H7 Z" fill="{BLUE}" stroke="{CYAN}" stroke-width="1"/>
  <text x="21" y="22" text-anchor="middle" font-family="monospace" font-size="11" font-weight="700" fill="{WHITE}">M</text>
  <circle cx="5.5" cy="0" r="4" fill="{GOLD}"/>
</g>

<!-- Ground -->
<line x1="28" y1="{TRACK_Y+31}" x2="{SVG_W-28}" y2="{TRACK_Y+31}" stroke="{GROUND_EDGE}" stroke-width="2" opacity="0.85"/>
<g>{ground}</g>

<!-- Original runner -->
<g transform="translate({start_x} {TRACK_Y})" filter="url(#glow)">
  <g transform="translate(0 -39) scale(1.25)">{pixel_runner()}</g>
  <animateMotion dur="{DURATION}s" repeatCount="indefinite" calcMode="linear" path="{path}"/>
</g>

<!-- Small dust pixels -->
<g fill="{CYAN}" opacity="0.65">
  <rect x="44" y="{TRACK_Y+24}" width="3" height="3"><animate attributeName="opacity" values="0;0.7;0" dur="0.8s" repeatCount="indefinite"/></rect>
  <rect x="51" y="{TRACK_Y+27}" width="2" height="2"><animate attributeName="opacity" values="0;0.5;0" dur="1.1s" repeatCount="indefinite"/></rect>
</g>

<!-- Finish message -->
<g opacity="0" filter="url(#glow)">
  <rect x="{SVG_W//2-118}" y="{TRACK_Y-126}" width="236" height="42" rx="8" fill="#081E34" stroke="{CYAN}"/>
  <text x="{SVG_W//2}" y="{TRACK_Y-99}" text-anchor="middle" font-family="monospace" font-size="18" font-weight="700" fill="{WHITE}">LEVEL COMPLETE</text>
  {complete_anim}
</g>

<text x="{SVG_W//2}" y="{SVG_H-14}" text-anchor="middle" font-family="monospace" font-size="10" fill="{MUTED}">generated from public GitHub contributions • refreshed automatically</text>
</svg>'''
    return svg


def demo_days() -> tuple[list[Day], int]:
    # Deterministic demo used only to ship an initial SVG before the first workflow run.
    days: list[Day] = []
    total = 0
    for week in range(53):
        for weekday in range(7):
            wave = math.sin(week * 0.42 + weekday * 0.93) + math.cos(week * 0.18 - weekday)
            count = 0
            if wave > 0.9:
                count = 1 + ((week + weekday) % 8)
            elif wave > 0.35 and (week + weekday) % 3 == 0:
                count = 1 + ((week * weekday + 2) % 4)
            total += count
            days.append(Day(week, weekday, count, f"demo-{week:02d}-{weekday}"))
    return days, total


def main() -> int:
    demo = "--demo" in sys.argv
    if demo:
        days, total = demo_days()
    else:
        data = graphql_request()
        days, total = parse_days(data)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(days, total), encoding="utf-8")
    print(f"Generated {OUTPUT} for {USER}: {total} contributions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
