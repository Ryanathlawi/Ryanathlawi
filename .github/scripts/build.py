import io, json, os, sys, urllib.request
from datetime import date, datetime

LOGIN = os.environ.get("PROFILE_LOGIN", "Ryanathlawi")
TOKEN = os.environ["GITHUB_TOKEN"]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, ".assets")
RAW = "https://raw.githubusercontent.com/{0}/{0}/main/.assets".format(LOGIN)
SITE = "https://athlawi.vercel.app"

W = 1000

THEMES = {
    "dark": dict(bg="#0d1117", grid="#171d25", name="#f0f6fc", sub="#8b949e",
                 muted="#6e7681", line="#21262d", red="#e5383b", deep="#6a040f",
                 glowop="0.30", streakop="1", cell="#161b22"),
    "light": dict(bg="#ffffff", grid="#eceff3", name="#0d1117", sub="#57606a",
                  muted="#8b949e", line="#d0d7de", red="#c1121f", deep="#9d0208",
                  glowop="0.16", streakop="0.5", cell="#eef1f4"),
}

QUERY = """
query($login:String!){
  user(login:$login){
    name
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false,
                 orderBy:{field:STARGAZERS, direction:DESC}){
      totalCount
      nodes{
        name description stargazerCount url
        primaryLanguage{name color}
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){edges{size node{name color}}}
      }
    }
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{firstDay contributionDays{date contributionCount weekday}}
      }
    }
  }
}
"""


def gql():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": "bearer " + TOKEN,
                 "Content-Type": "application/json",
                 "User-Agent": LOGIN})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit("GraphQL: " + json.dumps(payload["errors"]))
    return payload["data"]["user"]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def wrap(s, n):
    words, lines, cur = " ".join(s.split()).split(" "), [], ""
    for word in words:
        if cur and len(cur) + 1 + len(word) > n:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return lines


DESCRIPTIONS = {
    "wun-studio": "GTA V and FiveM toolkit — YTD texture editing, clothing validator, resource packing",
    "wun-cut": "Arabic desktop video editor that runs entirely offline",
}


def describe(repo):
    d = DESCRIPTIONS.get(repo["name"]) or repo.get("description") or ""
    if any(0x590 <= ord(c) <= 0x8ff or 0xfb1d <= ord(c) <= 0xfeff for c in d):
        d = ""
    return clip(d, 66)


def streaks(days):
    cur = best = run = 0
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    today = date.today().isoformat()
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["contributionCount"] > 0:
            cur += 1
        elif cur or d["date"] != today:
            break
    return cur, best


CSS = """.f{font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.m{font-family:'JetBrains Mono','Cascadia Mono',Consolas,'DejaVu Sans Mono',monospace}
.st{animation:sh 7s ease-in-out infinite}
.st2{animation-delay:.9s}.st3{animation-delay:1.8s}.st4{animation-delay:2.7s}.st5{animation-delay:3.6s}
@keyframes sh{0%,100%{opacity:.12}50%{opacity:.5}}
@keyframes rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}"""


def svg(w, h, t, body, css="", label=""):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        'role="img" aria-label="{label}">\n'
        "<defs>\n"
        '<pattern id="g" width="34" height="34" patternUnits="userSpaceOnUse">'
        '<path d="M34 0H0V34" fill="none" stroke="{grid}" stroke-width="1"/></pattern>\n'
        '<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="{red}"/><stop offset="100%" stop-color="{deep}"/></linearGradient>\n'
        '<linearGradient id="streak" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="{red}" stop-opacity="0"/>'
        '<stop offset="50%" stop-color="{red}" stop-opacity="{streakop}"/>'
        '<stop offset="100%" stop-color="{red}" stop-opacity="0"/></linearGradient>\n'
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="{red}" stop-opacity="{glowop}"/>'
        '<stop offset="100%" stop-color="{red}" stop-opacity="0"/></radialGradient>\n'
        '<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="{red}" stop-opacity="1"/>'
        '<stop offset="100%" stop-color="{red}" stop-opacity="0"/></linearGradient>\n'
        '<clipPath id="frame"><rect width="{w}" height="{h}" rx="8"/></clipPath>\n'
        "</defs>\n<style>{css}\n{extra}</style>\n{body}\n</svg>\n"
    ).format(w=w, h=h, label=esc(label), css=CSS, extra=css, body=body, **t)


def plate(w, h, t, glow_x=None):
    g = '<circle cx="{0}" cy="40" r="230" fill="url(#glow)"/>'.format(glow_x) if glow_x else ""
    return ('<rect width="{w}" height="{h}" fill="{bg}"/>'
            '<rect width="{w}" height="{h}" fill="url(#g)"/>{g}'
            '<rect x=".5" y=".5" width="{iw}" height="{ih}" rx="8" fill="none" stroke="{line}"/>'
            '<rect width="5" height="{h}" fill="url(#bar)"/>').format(
        w=w, h=h, iw=w - 1, ih=h - 1, g=g, bg=t["bg"], line=t["line"])


def streaks_art(x, y, h):
    out = []
    for dx, wd, cls in ((0, 2, ""), (58, 3, "st2"), (120, 2, "st3"), (184, 4, "st4"), (246, 2, "st5")):
        out.append('<rect class="st {0}" x="{1}" y="{2}" width="{3}" height="{4}" '
                   'fill="url(#streak)"/>'.format(cls, x + dx, y, wd, h))
    return '<g transform="rotate(22 {0} {1})">{2}</g>'.format(x + 130, y + h / 2, "".join(out))


def banner(t):
    lines = ["Building tools, systems, and clean interfaces",
             "Python · TypeScript · Lua · Go",
             "Dark UI, minimal design, readable code"]
    css = """.ln{animation:cyc 13.5s linear infinite}
.ln2,.ln3{opacity:0}.ln2{animation-delay:4.5s}.ln3{animation-delay:9s}
@keyframes cyc{0%{opacity:0}2%{opacity:1}31%{opacity:1}33%{opacity:0}100%{opacity:0}}
.cur{animation:blink 1.1s steps(1) infinite}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"""
    b = ['<g clip-path="url(#frame)">', plate(W, 260, t, 905), streaks_art(700, -140, 540),
         '<text class="m" x="56" y="80" font-size="13" letter-spacing="4.5" fill="{0}">'
         "// SELF-TAUGHT DEVELOPER</text>".format(t["red"]),
         '<text class="m" x="944" y="80" font-size="13" letter-spacing="3" fill="{0}" '
         'text-anchor="end">JEDDAH &#183; SAUDI ARABIA</text>'.format(t["muted"]),
         '<text class="f" x="54" y="153" font-size="54" font-weight="700" letter-spacing="5" '
         'fill="{0}">RYAN ATHLAWI</text>'.format(t["name"]),
         '<rect x="56" y="175" width="108" height="3" fill="{0}"/>'.format(t["red"])]
    for i, ln in enumerate(lines):
        cls = "ln" if i == 0 else "ln ln" + str(i + 1)
        b.append('<text class="m" x="56" y="217" font-size="18" fill="{0}">'
                 '<tspan class="{1}">{2}<tspan class="cur">_</tspan></tspan></text>'
                 .format(t["sub"], cls, esc(ln)))
    b.append("</g>")
    return svg(W, 260, t, "\n".join(b), css, "Ryan Athlawi")


def section(t, title, num):
    x = 46 + int(len(title) * 12.2)
    b = ['<rect x="0" y="18" width="14" height="14" fill="{0}"/>'.format(t["red"]),
         '<text class="m" x="28" y="31" font-size="17" font-weight="700" letter-spacing="4" '
         'fill="{0}">{1}</text>'.format(t["name"], esc(title.upper())),
         '<rect x="{0}" y="24" width="{1}" height="1.5" fill="url(#rule)"/>'.format(x, W - x - 70),
         '<text class="m" x="{0}" y="30" font-size="12" letter-spacing="2" fill="{1}" '
         'text-anchor="end">{2}</text>'.format(W - 26, t["muted"], num),
         '<circle cx="{0}" cy="25" r="4" fill="{1}" style="animation:pulse 3s ease-in-out infinite"/>'
         .format(W - 52, t["red"])]
    return svg(W, 50, t, "\n".join(b), "", title)


ABOUT = [("Desktop tools", "Python apps that do one job well — video editing, GTA V asset pipelines"),
         ("Game development", "FiveM systems in Lua, React-based NUI, tooling for QBCore / Qbox / ESX"),
         ("Web", "Next.js and TypeScript apps, REST APIs, Redis-backed services on Vercel"),
         ("Developer tooling", "VS Code extensions, Discord bots, automation for repeated work")]

INTRO = ("I build desktop tools, game-server systems, and web apps — mostly solo, end to end. "
         "My bias is toward clean architecture, dark minimal interfaces, and code that is still "
         "readable six months later.")


def about(t):
    h = 224
    css = ".rw{animation:rise .55s ease-out backwards}"
    b = ['<g clip-path="url(#frame)">', plate(W, h, t, 950), streaks_art(790, -100, 440)]
    for i, ln in enumerate(wrap(INTRO, 96)):
        b.append('<text class="m" x="40" y="{0}" font-size="14" fill="{1}">{2}</text>'
                 .format(44 + i * 22, t["sub"], esc(ln)))
    for i, (k, v) in enumerate(ABOUT):
        y = 118 + i * 26
        b.append('<g class="rw" style="animation-delay:{0:.2f}s">'
                 '<rect x="40" y="{1}" width="5" height="5" fill="{2}"/>'
                 '<text class="m" x="58" y="{3}" font-size="14" font-weight="700" fill="{4}">{5}</text>'
                 '<text class="m" x="238" y="{3}" font-size="14" fill="{6}">{7}</text></g>'
                 .format(0.08 * i, y - 9, t["red"], y, t["name"], esc(k), t["sub"], esc(v)))
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "About Ryan Athlawi")


STACK = [("LANGUAGES", ["Python", "TypeScript", "JavaScript", "Lua", "Go"]),
         ("FRAMEWORKS", ["Node.js", "React", "Next.js", "Express", "Qt"]),
         ("TOOLING", ["Git", "VS Code", "Vercel", "Redis", "Discord.js"])]


def stack(t):
    h = 232
    css = ".it{animation:rise .55s ease-out backwards}"
    b = ['<g clip-path="url(#frame)">', plate(W, h, t, 940), streaks_art(760, -120, 480)]
    n = 0
    for ci, (head, items) in enumerate(STACK):
        x = 56 + ci * 316
        b.append('<text class="m" x="{0}" y="52" font-size="13" letter-spacing="3.5" '
                 'fill="{1}">{2}</text>'.format(x, t["red"], head))
        b.append('<rect x="{0}" y="66" width="46" height="2" fill="{1}"/>'.format(x, t["red"]))
        for ii, item in enumerate(items):
            y = 104 + ii * 27
            b.append('<g class="it" style="animation-delay:{0:.2f}s">'
                     '<rect x="{1}" y="{2}" width="5" height="5" fill="{3}"/>'
                     '<text class="m" x="{4}" y="{5}" font-size="15" fill="{6}">{7}</text></g>'
                     .format(0.06 * n, x, y - 9, t["red"], x + 16, y, t["sub"], esc(item)))
            n += 1
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "Tech stack")


def project(t, repo, idx):
    h = 104
    css = ('.ar{animation:slide 2.6s ease-in-out infinite}'
           '@keyframes slide{0%,100%{transform:translateX(0);opacity:.45}'
           '50%{transform:translateX(6px);opacity:1}}')
    lang = repo.get("primaryLanguage") or {}
    rx = W - 44
    desc = describe(repo)
    b = ['<g clip-path="url(#frame)">', plate(W, h, t, 1010), streaks_art(892, -60, 260),
         '<text class="m" x="40" y="42" font-size="12" letter-spacing="3" fill="{0}">{1:02d}</text>'
         .format(t["muted"], idx),
         '<text class="m" x="76" y="44" font-size="21" font-weight="700" fill="{0}">{1}</text>'
         .format(t["name"], esc(repo["name"])),
         '<text class="m" x="76" y="72" font-size="14" fill="{0}">{1}</text>'.format(t["sub"], esc(desc)),
         '<path class="ar" d="M{0} 44h16m-6-6 6 6-6 6" fill="none" stroke="{1}" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"/>'.format(rx - 22, t["red"])]
    if lang.get("name"):
        b.append('<circle cx="{0}" cy="68" r="5" fill="{1}"/>'
                 .format(rx - 128, lang.get("color") or t["red"]))
        b.append('<text class="m" x="{0}" y="73" font-size="13" fill="{1}">{2}</text>'
                 .format(rx - 116, t["sub"], esc(lang["name"])))
    b.append('<path d="M{0} 63.5l2.2 4.4 4.9.7-3.6 3.4.9 4.8-4.4-2.3-4.4 2.3.9-4.8-3.6-3.4 4.9-.7z" '
             'fill="{1}"/>'.format(rx - 42, t["red"]))
    b.append('<text class="m" x="{0}" y="73" font-size="13" fill="{1}" text-anchor="end">{2}</text>'
             .format(rx, t["sub"], repo["stargazerCount"]))
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "{0}: {1}".format(repo["name"], desc))


def stats(t, m):
    h = 176
    css = ('.un{animation:grow 1.1s ease-out backwards}'
           '@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}'
           '.nb{animation:rise .7s ease-out backwards}')
    b = ['<g clip-path="url(#frame)">', plate(W, h, t, 900), streaks_art(770, -80, 380),
         '<text class="m" x="40" y="42" font-size="13" letter-spacing="3.5" fill="{0}">'
         "// LAST 12 MONTHS</text>".format(t["red"])]
    cells = [("CONTRIBUTIONS", m["contribs"]), ("CURRENT STREAK", m["cur"]),
             ("LONGEST STREAK", m["best"]), ("PUBLIC REPOS", m["repos"]),
             ("TOTAL STARS", m["stars"])]
    step = (W - 80) / 5.0
    for i, (label, val) in enumerate(cells):
        cx = 40 + step * i + step / 2
        if i:
            b.append('<rect x="{0:.1f}" y="70" width="1" height="74" fill="{1}"/>'
                     .format(40 + step * i, t["line"]))
        b.append('<g class="nb" style="animation-delay:{0:.2f}s">'
                 '<text class="f" x="{1:.1f}" y="116" font-size="40" font-weight="700" fill="{2}" '
                 'text-anchor="middle">{3}</text>'
                 '<text class="m" x="{1:.1f}" y="138" font-size="11" letter-spacing="2" fill="{4}" '
                 'text-anchor="middle">{5}</text></g>'
                 .format(0.1 * i, cx, t["name"], val, t["muted"], label))
        b.append('<rect class="un" x="{0:.1f}" y="150" width="34" height="2.5" fill="{1}" '
                 'style="animation-delay:{2:.2f}s;transform-origin:{3:.1f}px 0"/>'
                 .format(cx - 17, t["red"], 0.1 * i, cx))
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "GitHub statistics")


def languages(t, langs):
    h = 102 + 26 * ((len(langs[:6]) + 2) // 3)
    css = ('.seg{animation:wide .9s cubic-bezier(.2,.8,.2,1) backwards}'
           '@keyframes wide{from{transform:scaleX(0)}to{transform:scaleX(1)}}'
           '.lg{animation:fade .6s ease-out backwards}')
    total = float(sum(s for _, _, s in langs)) or 1.0
    bx, bw = 40, W - 80
    b = ['<clipPath id="lb"><rect x="{0}" y="60" width="{1}" height="16" rx="8"/></clipPath>'
         .format(bx, bw),
         '<g clip-path="url(#frame)">', plate(W, h, t, 930),
         '<text class="m" x="40" y="42" font-size="13" letter-spacing="3.5" fill="{0}">'
         "// LANGUAGE DISTRIBUTION</text>".format(t["red"]),
         '<rect x="{0}" y="60" width="{1}" height="16" rx="8" fill="{2}"/>'.format(bx, bw, t["cell"])]
    off, parts = 0.0, []
    for i, (nm, col, size) in enumerate(langs):
        wpx = bw * size / total
        parts.append('<rect class="seg" x="{0:.2f}" y="60" width="{1:.2f}" height="16" fill="{2}" '
                     'style="animation-delay:{3:.2f}s;transform-origin:{0:.2f}px 0"/>'
                     .format(bx + off, wpx, col, 0.08 * i))
        off += wpx
    b.append('<g clip-path="url(#lb)">{0}</g>'.format("".join(parts)))
    for i, (nm, col, size) in enumerate(langs[:6]):
        x = 40 + (i % 3) * 316
        y = 110 + (i // 3) * 26
        b.append('<g class="lg" style="animation-delay:{0:.2f}s">'
                 '<circle cx="{1}" cy="{2}" r="5" fill="{3}"/>'
                 '<text class="m" x="{4}" y="{5}" font-size="14" fill="{6}">{7}</text>'
                 '<text class="m" x="{8}" y="{5}" font-size="14" fill="{9}">{10:.1f}%</text></g>'
                 .format(0.5 + 0.07 * i, x + 6, y - 4, col, x + 20, y, t["sub"], esc(nm),
                         x + 240, t["muted"], 100.0 * size / total))
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "Language distribution")


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def mix(fg, bg, f):
    a = tuple(int(fg[i:i + 2], 16) for i in (1, 3, 5))
    c = tuple(int(bg[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c[i] + (a[i] - c[i]) * f) for i in range(3))


def activity(t, weeks):
    cs, gap, top, left = 12, 3, 58, 64
    h = top + 7 * (cs + gap) + 46
    css = ".cl{animation:fade .5s ease-out backwards}"
    peak = max([d["contributionCount"] for w in weeks for d in w["contributionDays"]] + [1])
    steps = [mix(t["red"], t["bg"], f) for f in (0.3, 0.52, 0.76, 1.0)]
    b = ['<g clip-path="url(#frame)">', plate(W, h, t),
         '<text class="m" x="40" y="34" font-size="13" letter-spacing="3.5" fill="{0}">'
         "// CONTRIBUTION ACTIVITY</text>".format(t["red"])]
    last = None
    for wi, wk in enumerate(weeks):
        x = left + wi * (cs + gap)
        month = datetime.strptime(wk["firstDay"], "%Y-%m-%d").month
        if month != last and wi < len(weeks) - 1:
            b.append('<text class="m" x="{0}" y="{1}" font-size="11" fill="{2}">{3}</text>'
                     .format(x, top - 10, t["muted"], MONTHS[month - 1]))
            last = month
        for d in wk["contributionDays"]:
            y = top + d["weekday"] * (cs + gap)
            c = d["contributionCount"]
            if c == 0:
                fill = t["cell"]
            elif peak <= 4:
                fill = steps[min(3, c)]
            else:
                fill = steps[min(3, int(4.0 * c / peak))]
            b.append('<rect class="cl" x="{0}" y="{1}" width="{2}" height="{2}" rx="2.5" fill="{3}" '
                     'style="animation-delay:{4:.2f}s"/>'.format(x, y, cs, fill, 0.012 * wi))
    for wd, nm in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b.append('<text class="m" x="46" y="{0}" font-size="11" fill="{1}" '
                 'text-anchor="end">{2}</text>'.format(top + wd * (cs + gap) + 10, t["muted"], nm))
    lx = W - 200
    b.append('<text class="m" x="{0}" y="{1}" font-size="11" fill="{2}">Less</text>'
             .format(lx, h - 18, t["muted"]))
    b.append('<rect x="{0}" y="{1}" width="11" height="11" rx="2.5" fill="{2}"/>'
             .format(lx + 34, h - 28, t["cell"]))
    for i, c in enumerate(steps):
        b.append('<rect x="{0}" y="{1}" width="11" height="11" rx="2.5" fill="{2}"/>'
                 .format(lx + 34 + (i + 1) * 15, h - 28, c))
    b.append('<text class="m" x="{0}" y="{1}" font-size="11" fill="{2}">More</text>'
             .format(lx + 128, h - 18, t["muted"]))
    b.append("</g>")
    return svg(W, h, t, "\n".join(b), css, "Contribution activity")


def button(t, label, sub):
    w, h = 300, 62
    css = ".dt{animation:pulse 2.6s ease-in-out infinite}"
    b = ['<rect x="1" y="1" width="{0}" height="{1}" rx="8" fill="{2}" stroke="{3}"/>'
         .format(w - 2, h - 2, t["bg"], t["line"]),
         '<rect x="1" y="1" width="5" height="{0}" fill="url(#bar)"/>'.format(h - 2),
         '<text class="m" x="26" y="27" font-size="11" letter-spacing="3" fill="{0}">{1}</text>'
         .format(t["red"], esc(label)),
         '<text class="m" x="26" y="47" font-size="14" fill="{0}">{1}</text>'.format(t["name"], esc(sub)),
         '<circle class="dt" cx="{0}" cy="31" r="4" fill="{1}"/>'.format(w - 26, t["red"]),
         '<path d="M{0} 28l7-7m0 0h-5.5m5.5 0v5.5" fill="none" stroke="{1}" stroke-width="1.6" '
         'stroke-linecap="round"/>'.format(w - 58, t["muted"])]
    return svg(w, h, t, "\n".join(b), css, "{0}: {1}".format(label, sub))


def footer(t):
    h = 86
    css = ".dt{animation:pulse 3s ease-in-out infinite}"
    b = ['<linearGradient id="fr" x1="0" y1="0" x2="1" y2="0">'
         '<stop offset="0%" stop-color="{0}" stop-opacity="0"/>'
         '<stop offset="50%" stop-color="{1}" stop-opacity="1"/>'
         '<stop offset="100%" stop-color="{0}" stop-opacity="0"/></linearGradient>'
         .format(t["deep"], t["red"]),
         '<rect x="0" y="30" width="{0}" height="2" fill="url(#fr)"/>'.format(W),
         '<circle class="dt" cx="{0}" cy="31" r="4.5" fill="{1}"/>'.format(W // 2, t["red"]),
         '<text class="m" x="{0}" y="66" font-size="12" letter-spacing="3" fill="{1}" '
         'text-anchor="middle">THANKS FOR STOPPING BY</text>'.format(W // 2, t["muted"])]
    return svg(W, h, t, "\n".join(b), css, "")


def pic(base, alt, width="100%"):
    return ('<picture>\n'
            '  <source media="(prefers-color-scheme: dark)" srcset="{raw}/{b}-dark.svg" />\n'
            '  <source media="(prefers-color-scheme: light)" srcset="{raw}/{b}-light.svg" />\n'
            '  <img src="{raw}/{b}-dark.svg" width="{w}" alt="{alt}" />\n'
            '</picture>').format(raw=RAW, b=base, w=width, alt=esc(alt))


def readme(repos):
    p = ['<div align="center">\n',
         pic("banner", "Ryan Athlawi — self-taught developer, Jeddah, Saudi Arabia"),
         "\n</div>\n",
         pic("sec-about", "About"), "\n", pic("about", INTRO), "\n",
         pic("sec-stack", "Tech Stack"), "\n", pic("stack", "Tech stack"), "\n",
         pic("sec-projects", "Featured Projects"), "\n"]
    for r in repos:
        p.append('<a href="{0}">{1}</a>\n'.format(
            r["url"], pic("proj-" + r["name"],
                          "{0}: {1}".format(r["name"], describe(r)))))
    p += [pic("sec-stats", "GitHub Stats"), "\n", pic("stats", "GitHub statistics"), "\n",
          pic("langs", "Language distribution"), "\n", pic("activity", "Contribution activity"), "\n",
          pic("sec-connect", "Connect"), "\n", '<div align="center">\n',
          '<a href="{0}">{1}</a>\n'.format(SITE, pic("btn-site", "Portfolio: athlawi.vercel.app", "300")),
          '<a href="https://github.com/{0}?tab=repositories">{1}</a>\n'.format(
              LOGIN, pic("btn-repos", "GitHub: all repositories", "300")),
          "\n", pic("footer", ""), "\n</div>\n"]
    return "\n".join(p)


SECTIONS = [("about", "About", "01"), ("stack", "Tech Stack", "02"),
            ("projects", "Featured Projects", "03"), ("stats", "GitHub Stats", "04"),
            ("connect", "Connect", "05")]


def main():
    user = gql()
    nodes = [r for r in user["repositories"]["nodes"] if r["name"].lower() != LOGIN.lower()]
    repos = nodes[:4]
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    cur, best = streaks([d for w in weeks for d in w["contributionDays"]])
    metrics = dict(contribs=cal["totalContributions"], cur=cur, best=best,
                   repos=user["repositories"]["totalCount"],
                   stars=sum(r["stargazerCount"] for r in nodes))
    sizes = {}
    for r in nodes:
        for e in r["languages"]["edges"]:
            nm = e["node"]["name"]
            prev, col = sizes.get(nm, (0, e["node"]["color"] or "#8b949e"))
            sizes[nm] = (prev + e["size"], col)
    langs = sorted([(nm, c, s) for nm, (s, c) in sizes.items()], key=lambda x: -x[2])[:6]

    os.makedirs(OUT, exist_ok=True)
    for theme_name, t in THEMES.items():
        def write(base, content):
            path = os.path.join(OUT, "{0}-{1}.svg".format(base, theme_name))
            io.open(path, "w", encoding="utf-8").write(content)

        write("banner", banner(t))
        write("about", about(t))
        write("stack", stack(t))
        write("stats", stats(t, metrics))
        write("langs", languages(t, langs))
        write("activity", activity(t, weeks))
        write("footer", footer(t))
        write("btn-site", button(t, "PORTFOLIO", "athlawi.vercel.app"))
        write("btn-repos", button(t, "GITHUB", "All repositories"))
        for key, title, num in SECTIONS:
            write("sec-" + key, section(t, title, num))
        for i, r in enumerate(repos, 1):
            write("proj-" + r["name"], project(t, r, i))

    io.open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme(repos))
    print("repos={0} langs={1} contribs={2} streak={3}/{4} stars={5}".format(
        len(repos), len(langs), metrics["contribs"], cur, best, metrics["stars"]))


main()
