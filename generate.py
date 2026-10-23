"""
Project Pulse - synthetic data generator (Icreon CDA 650, Brief 3)
====================================================================
Creates fictional, i360-style project status data, Jira-style issues/sprints/changelog,
and Hindi-English (Hinglish) meeting transcripts with screen-OCR frames.

Key design rule: every project has a HIDDEN "true health" curve. Jira signals and the
typed i360 status are both *generated from* that hidden truth (with noise, lag and bias).
Your detector never sees the hidden truth - it is only used to score the detector.

Run:  python generate.py            (defaults below)
      python generate.py --seed 7 --n_hist 150 --n_live 10
"""
import argparse, json, math, os, random
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from vocab import *

# ----------------------------------------------------------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--n_hist", type=int, default=60, help="completed historical projects")
ap.add_argument("--n_live", type=int, default=8, help="in-flight projects")
ap.add_argument("--today", default="2026-10-16")
ap.add_argument("--out", default="data")
ARGS = ap.parse_args()

R = random.Random(ARGS.seed)
NP = np.random.default_rng(ARGS.seed)
TODAY = datetime.fromisoformat(ARGS.today).replace(hour=18)
OUT = ARGS.out
for d in ["", "gold", "hidden"]:
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

SCENARIOS = ["healthy", "slow_burn", "sudden_shock", "client_blocked", "recovering"]
SCEN_P = [0.35, 0.2, 0.15, 0.15, 0.15]
STATUS_FLOW = ["To Do", "In Progress", "In Review", "QA", "Done"]
PRIORITIES = ["Lowest", "Low", "Medium", "High", "Highest"]
LEAD_TRAITS = {l: dict(optimism=float(NP.uniform(0.0, 0.25)), lag=int(R.choice([1, 2, 2, 3])))
               for l in DELIVERY_LEADS}


def monday(d):
    return (d - timedelta(days=d.weekday())).replace(hour=9, minute=0, second=0, microsecond=0)


def clip(x, a, b):
    return max(a, min(b, x))


def rag(h):
    return "Green" if h >= 0.65 else ("Yellow" if h >= 0.40 else "Red")


# ----------------------------------------------------------------------------------
# 1. Projects + hidden health curves
# ----------------------------------------------------------------------------------
def health_curve(scen, W):
    h = np.zeros(W)
    onset = int(W * R.uniform(0.25, 0.55))
    base = R.uniform(0.78, 0.9)
    noise = 0.0
    blocks = []
    if scen == "client_blocked":
        t = R.randint(2, max(3, W // 3))
        while t < W:
            ln = R.randint(2, 4)
            blocks.append((t, t + ln))
            t += ln + R.randint(3, 7)
    rec_at = onset + R.randint(3, 6)
    for t in range(W):
        noise = 0.6 * noise + NP.normal(0, 0.035)
        v = base
        if scen == "slow_burn" and t >= onset:
            v = base - (t - onset) * R.uniform(0.035, 0.06)
        elif scen == "sudden_shock" and t >= onset:
            v = base - 0.45 + 0.012 * (t - onset)
        elif scen == "client_blocked" and any(a <= t < b for a, b in blocks):
            v = base - R.uniform(0.35, 0.5)
        elif scen == "recovering":
            if onset <= t < rec_at:
                v = base - (t - onset + 1) * 0.11
            elif t >= rec_at:
                v = min(base, base - (rec_at - onset) * 0.11 + (t - rec_at + 1) * 0.07)
        elif scen == "healthy" and R.random() < 0.05:
            v = base - 0.2  # one-off bad week that should NOT trigger red
        h[t] = clip(v + noise, 0.05, 0.98)
    return h, dict(onset_week=onset, block_windows=blocks, recovery_week=rec_at if scen == "recovering" else None)


def loc_value(live):
    loc = R.choices(["US", "UK", "India"], [0.75, 0.1, 0.15] if live else [0.5, 0.2, 0.3])[0]
    messy = {"US": ["US", "US", "USA", "United States"], "UK": ["UK", "UK", "United Kingdom"],
             "India": ["India", "India", "IN"]}
    return R.choice(messy[loc])


projects, hidden_health, hidden_meta = [], [], []
used_keys = set()
for i in range(ARGS.n_hist + ARGS.n_live):
    live = i >= ARGS.n_hist
    showcase = (i == ARGS.n_hist)  # first live project = demo project
    if showcase:
        ptype, key, client, scen = "Membership Portal", "HMP", "Harborview Museum", "client_blocked"
    else:
        ptype, key = R.choice(PROJECT_TYPES)
        client = R.choice(CLIENTS)
        scen = R.choices(SCENARIOS, SCEN_P)[0]
    k = key
    n = 0
    while k in used_keys:
        n += 1
        k = key + chr(64 + n)
    used_keys.add(k)
    if live:
        cur_w = 14 if showcase else R.randint(6, 22)
        planned_w = max(cur_w + R.randint(4, 14), 16)
        start = monday(TODAY - timedelta(weeks=cur_w - 1))
        W = cur_w
    else:
        planned_w = R.randint(12, 34)
        latest = TODAY - timedelta(weeks=planned_w + 8)
        start = monday(datetime(2024, 1, 8) + timedelta(days=R.randint(0, max(1, (latest - datetime(2024, 1, 8)).days))))
        W = planned_w
    lead = R.choice(DELIVERY_LEADS)
    h, meta = health_curve(scen, W)
    pid = f"P{1000 + i}"
    projects.append(dict(project_id=pid, project_name=f"{client} - {ptype}", client=client, jira_key=k,
                         location=loc_value(live), criticality=R.choices(["Normal", "Critical"], [0.75, 0.25])[0],
                         delivery_lead=lead, team_size=R.randint(3, 9), start_date=start.date().isoformat(),
                         planned_end_date=(start + timedelta(weeks=planned_w)).date().isoformat(),
                         planned_weeks=planned_w, state="Active" if live else "Closed",
                         methodology=R.choices(["Scrum", "Kanban-ish", "Scrum"], [0.6, 0.15, 0.25])[0],
                         budget_hours=int(planned_w * R.randint(80, 260))))
    hidden_meta.append(dict(project_id=pid, scenario=scen, **{kk: json.dumps(v) if isinstance(v, list) else v
                                                                for kk, v in meta.items()}))
    for t in range(W):
        hidden_health.append(dict(project_id=pid, week_index=t,
                                  week_ending=(start + timedelta(weeks=t, days=4)).date().isoformat(),
                                  true_health_score=round(float(h[t]), 3), true_rag=rag(h[t])))

P = pd.DataFrame(projects)
H = pd.DataFrame(hidden_health)
HM = pd.DataFrame(hidden_meta)
hcurve = {pid: g.sort_values("week_index").true_health_score.values for pid, g in H.groupby("project_id")}
scen_of = dict(zip(HM.project_id, HM.scenario))
meta_of = {r.project_id: r for r in HM.itertuples()}

# ----------------------------------------------------------------------------------
# 2. Typed i360 status (lagging + optimistic + sticky + messy)
# ----------------------------------------------------------------------------------
status_rows = []
typed_status_at = {}  # (pid, week) -> clean status
for p in P.itertuples():
    tr = LEAD_TRAITS[p.delivery_lead]
    bias = tr["optimism"] * (0.5 if p.criticality == "Critical" else 1.0)
    h = hcurve[p.project_id]
    cur = "Green"
    start = datetime.fromisoformat(p.start_date)
    for t in range(len(h)):
        perceived = h[max(0, t - tr["lag"])] + bias + NP.normal(0, 0.04)
        if cur == "Green" and perceived < 0.52: cur = "Yellow"
        elif cur == "Yellow" and perceived < 0.30: cur = "Red"
        elif cur == "Yellow" and perceived > 0.70: cur = "Green"
        elif cur == "Red" and perceived > 0.45: cur = "Yellow"
        typed_status_at[(p.project_id, t)] = cur
        week_end = start + timedelta(weeks=t, days=4)
        skip_p = 0.08 + (0.12 if h[t] < 0.45 else 0)
        if R.random() < skip_p:
            continue  # nobody updated i360 this week
        shown = cur
        r = R.random()
        if r < 0.04: shown = cur.lower()
        elif r < 0.07: shown = cur[0]
        elif r < 0.10 and cur == "Yellow": shown = "Amber"
        entered = week_end + timedelta(days=R.choice([0, 0, 0, 1, 3, 5]), hours=R.randint(0, 9))
        status_rows.append(dict(project_id=p.project_id, week_ending=week_end.date().isoformat(),
                                typed_status=shown, status_comment=R.choice(STATUS_COMMENTS[cur]),
                                entered_by=p.delivery_lead, entered_at=entered.isoformat(timespec="minutes")))
S = pd.DataFrame(status_rows)

# ----------------------------------------------------------------------------------
# 3. Jira: sprints, issues, changelog, comments
# ----------------------------------------------------------------------------------
sprint_rows, issue_rows, events, comments = [], [], [], []
iid = 0


def fmt_ts(ts):
    # 5% of timestamps come in Jira's export format - deliberate mess
    return ts.strftime("%d/%b/%y %I:%M %p") if R.random() < 0.05 else ts.isoformat(timespec="minutes")


def team_for(p):
    pool = INDIA_PEOPLE + (US_UK_PEOPLE if p.location not in ("India", "IN") else [])
    rr = random.Random(ARGS.seed * 100_000 + int(p.project_id[1:]))
    return rr.sample(pool, p.team_size)


TEAM = {p.project_id: team_for(p) for p in P.itertuples()}
for p in P.itertuples():
    pid, h = p.project_id, hcurve[p.project_id]
    scen = scen_of[pid]
    meta = meta_of[pid]
    team = list(TEAM[pid])
    start = datetime.fromisoformat(p.start_date)
    live = p.state == "Active"
    n_sprints = math.ceil(len(h) / 2)
    open_tix = []
    departed = None
    if scen == "sudden_shock":
        departed = R.choice(team)
    forced = {}
    for s in range(n_sprints):
        s_start = start + timedelta(days=14 * s)
        s_end = s_start + timedelta(days=13, hours=8)
        hs = float(np.mean(h[2 * s: 2 * s + 2]))
        week0 = 2 * s
        blocked_window = any(a <= week0 < b for a, b in json.loads(meta.block_windows)) if scen == "client_blocked" else False
        sid = f"{p.jira_key}-S{s + 1}"
        active_team = [m for m in team if not (departed and week0 >= meta.onset_week and m == departed)]
        target = len(active_team) * NP.normal(7, 1.0)
        sprint_tix = [t for t in open_tix]
        pts = sum(t["points"] or 3 for t in sprint_tix)
        for t in sprint_tix:  # carry-over sprint move event
            events.append((t["id"], s_start + timedelta(hours=1), "Sprint", t["sprint"], sid, p.delivery_lead))
            t["sprint"] = sid
            t["sprints"].append(sid)

        def new_ticket(created, itype=None, tmpl=None):
            global iid
            iid += 1
            tmpl = tmpl or R.choice(TICKET_TEMPLATES)
            itype = itype or R.choices(["Story", "Task", "Bug"], [0.55, 0.25, 0.2])[0]
            pts_ = R.choice([1, 2, 3, 3, 5, 5, 8, 13]) if itype != "Bug" else R.choice([None, 1, 2, 3])
            if R.random() < 0.15: pts_ = None
            t = dict(id=iid, pid=pid, summary=tmpl[0], short=tmpl[1], kw=tmpl[2], type=itype, points=pts_,
                     assignee=R.choice(active_team), reporter=R.choice([p.delivery_lead] + active_team),
                     priority=R.choices(PRIORITIES, [0.05, 0.2, 0.45, 0.22, 0.08])[0], status="To Do",
                     created=created, sprint=sid, component=R.choice(COMPONENTS), labels=[], dep=None, sprints=[sid])
            if R.random() < 0.08: t["assignee"] = None
            issue_rows.append(t)
            events.append((t["id"], created, "created", None, "To Do", t["reporter"]))
            return t

        # showcase hooks: HMP-4000 created in sprint 2 (stays blocked); HMP-5500 created in the current sprint
        if pid == P.project_id.iloc[ARGS.n_hist]:
            if s == 1:
                t = new_ticket(s_start + timedelta(hours=3), "Story", TICKET_TEMPLATES[0])
                t.update(points=5, priority="High", assignee="Rohan Mehta" if "Rohan Mehta" in team else team[0])
                forced[t["id"]] = "4000"
                sprint_tix.append(t)
                pts += 5
            if s == n_sprints - 1:
                t = new_ticket(s_start + timedelta(hours=4), "Story", TICKET_TEMPLATES[1])
                t.update(points=8, priority="Medium", assignee=R.choice([m for m in team if m != t["assignee"]] or team))
                forced[t["id"]] = "5500"
                sprint_tix.append(t)
                pts += 8
        while pts < target:
            t = new_ticket(s_start - timedelta(days=R.randint(0, 20), hours=R.randint(0, 8)))
            sprint_tix.append(t)
            pts += t["points"] or 3
        # mid-sprint scope additions + bugs
        creep = 0.4 + (3.0 * (1 - hs) if scen == "slow_burn" and week0 >= meta.onset_week else 0)
        for _ in range(NP.poisson(creep)):
            sprint_tix.append(new_ticket(s_start + timedelta(days=R.uniform(1, 9))))
        for _ in range(NP.poisson(0.8 + 4 * (1 - hs))):
            sprint_tix.append(new_ticket(s_start + timedelta(days=R.uniform(0, 11)), "Bug"))
        completed_pts = 0
        committed_pts = sum(t["points"] or 0 for t in sprint_tix if t["created"] <= s_start + timedelta(hours=6))
        sprint_rows.append(dict(sprint_id=sid, project_id=pid, jira_key=p.jira_key, sprint_name=f"{p.jira_key} Sprint {s + 1}",
                                start_date=s_start.date().isoformat(), end_date=s_end.date().isoformat(),
                                goal=R.choice(["Finish checkout flow", "UAT readiness", "Integration milestone",
                                               "Bug bash + release", "Content migration", "Performance hardening", ""]),
                                committed_points=committed_pts))
        open_tix = []
        for t in sprint_tix:
            if departed and week0 >= meta.onset_week and t["assignee"] == departed:
                newp = R.choice(active_team)
                events.append((t["id"], s_start + timedelta(days=R.uniform(0, 2)), "assignee", departed, newp, p.delivery_lead))
                t["assignee"] = newp
            if forced.get(t["id"]) == "4000":
                # stuck: client still hasn't configured SSO
                if t["status"] == "To Do":
                    ts = s_start + timedelta(days=1)
                    events.append((t["id"], ts, "status", "To Do", "In Progress", t["assignee"]))
                    events.append((t["id"], ts + timedelta(days=3), "status", "In Progress", "Blocked", t["assignee"]))
                    t["status"] = "Blocked"
                    t["dep"] = "SSO config from client IT"
                    t["labels"] = ["blocked"]
                open_tix.append(t)
                continue
            if forced.get(t["id"]) == "5500":
                ts = s_start + timedelta(days=1, hours=2)
                events.append((t["id"], ts, "status", "To Do", "In Progress", t["assignee"]))
                t["status"] = "In Progress"
                continue
            p_done = clip(0.25 + 0.72 * hs - 0.03 * ((t["points"] or 3) - 3), 0.05, 0.96)
            p_block = (1 - hs) * 0.22 + (0.35 if blocked_window else 0)
            cur_t = max(t["created"], s_start) + timedelta(hours=R.uniform(2, 60))
            cyc = R.uniform(0.6, 3.0) * (1 + 1.5 * (1 - hs)) * (1 + (t["points"] or 3) / 8)
            if t["status"] in ("To Do", "Reopened", "Blocked"):
                events.append((t["id"], cur_t, "status", t["status"], "In Progress", t["assignee"] or p.delivery_lead))
                t["status"] = "In Progress"
            if R.random() < p_block:
                bt = cur_t + timedelta(days=R.uniform(0.3, 2))
                events.append((t["id"], bt, "status", t["status"], "Blocked", t["assignee"] or p.delivery_lead))
                t["status"] = "Blocked"
                t["dep"] = R.choice(DEPENDENCIES)
                t["labels"] = [R.choice(["blocked", "Blocked", "BLOCKER", "client-dependency", "waiting-on-client", ""])]
                if R.random() < 0.45:
                    ut = bt + timedelta(days=R.uniform(1, 5))
                    if ut < s_end:
                        events.append((t["id"], ut, "status", "Blocked", "In Progress", t["assignee"] or p.delivery_lead))
                        t["status"] = "In Progress"
                        cur_t = ut
                if t["status"] == "Blocked":
                    open_tix.append(t)
                    continue
            if R.random() < (1 - hs) * 0.08:
                newpri = PRIORITIES[min(4, PRIORITIES.index(t["priority"]) + 1)]
                if newpri != t["priority"]:
                    events.append((t["id"], cur_t + timedelta(hours=5), "priority", t["priority"], newpri, p.delivery_lead))
                    t["priority"] = newpri
            if R.random() < 0.05 and t["points"]:
                newpts = R.choice([2, 3, 5, 8, 13])
                events.append((t["id"], cur_t + timedelta(hours=7), "Story Points", t["points"], newpts, t["assignee"] or p.delivery_lead))
                t["points"] = newpts
            if R.random() < p_done:
                steps = ["In Review", "QA", "Done"]
                tt = cur_t
                for st in steps:
                    tt = tt + timedelta(days=cyc / 3)
                    events.append((t["id"], min(tt, s_end - timedelta(hours=1)), "status", t["status"], st, t["assignee"] or p.delivery_lead))
                    t["status"] = st
                if R.random() < (1 - hs) * 0.2:
                    rt = min(tt + timedelta(days=R.uniform(0.5, 3)), s_end - timedelta(minutes=30))
                    events.append((t["id"], rt, "status", "Done", "Reopened", R.choice(active_team)))
                    t["status"] = "Reopened"
                    comments.append((t["id"], rt, R.choice(active_team), R.choice(TICKET_COMMENTS["reopen"])))
                    open_tix.append(t)
                else:
                    completed_pts += t["points"] or 0
            else:
                if R.random() < 0.5:
                    st = R.choice(["In Review", "QA"])
                    events.append((t["id"], cur_t + timedelta(days=cyc / 2), "status", t["status"], st, t["assignee"] or p.delivery_lead))
                    t["status"] = st
                open_tix.append(t)
        sprint_rows[-1]["completed_points_reported"] = completed_pts if R.random() > 0.1 else None
    # backlog: future work not yet pulled into a sprint
    if live:
        for _ in range(p.team_size * R.randint(2, 5)):
            t = new_ticket(start + timedelta(days=R.uniform(0, 7 * len(h))))
            t["sprint"] = None
            t["sprints"] = []
    # historical close-out: remaining tickets done in a crunch or won't-do
    if not live:
        end = start + timedelta(weeks=len(h))
        for t in open_tix:
            ts = end - timedelta(days=R.uniform(0, 4))
            final = "Done" if R.random() < 0.7 else "Won't Do"
            events.append((t["id"], ts, "status", t["status"], final, p.delivery_lead))
    for tid, num in forced.items():
        for t in issue_rows:
            if t["id"] == tid:
                t["forced_num"] = int(num)

# ---- cut everything after TODAY, rebuild final ticket state from the event log ----
events = [e for e in events if e[1] <= TODAY]
comments = [c for c in comments if c[1] <= TODAY]
issue_rows = [t for t in issue_rows if t["created"] <= TODAY]
last_status, done_at, created_at = {}, {}, {}
for e in sorted(events, key=lambda e: e[1]):
    if e[2] in ("status", "created"):
        last_status[e[0]] = e[4]
        if e[4] in ("Done", "Won't Do"):
            done_at[e[0]] = e[1]
        elif e[0] in done_at:
            del done_at[e[0]]

# ---- assign issue keys (with gaps), keep showcase keys 4000 / 5500 ----
key_of = {}
by_proj = defaultdict(list)
for t in issue_rows:
    by_proj[t["pid"]].append(t)
jkey = dict(zip(P.project_id, P.jira_key))
for pid, ts in by_proj.items():
    ts.sort(key=lambda t: t["created"])
    num = R.randint(1, 2500) if jkey[pid] != "HMP" else 3961
    reserved = {t.get("forced_num") for t in ts if t.get("forced_num")}
    for j, t in enumerate(ts):
        if t.get("forced_num"):
            key_of[t["id"]] = f"{jkey[pid]}-{t['forced_num']}"
            continue
        num += 1 + (R.random() < 0.08) * R.randint(1, 4)
        if jkey[pid] == "HMP" and j == len(ts) // 3:
            num = 5401  # board merge in sprint ~5 - numbers jump (a real Jira quirk)
        while num in reserved:
            num += 1
        key_of[t["id"]] = f"{jkey[pid]}-{num}"

# ---- duplicates (deliberate mess) ----
dups = []
for t in R.sample(issue_rows, int(len(issue_rows) * 0.03)):
    iid += 1
    d = dict(t, id=iid, summary=t["summary"] + R.choice(["", " ", " (copy)", " - dup"]), labels=["duplicate"] if R.random() < 0.3 else [])
    key_of[iid] = key_of[t["id"]].split("-")[0] + f"-{int(key_of[t['id']].split('-')[1]) + 7000}"
    last_status[iid] = "Closed"
    events.append((iid, t["created"] + timedelta(days=1), "created", None, "To Do", t["reporter"]))
    events.append((iid, t["created"] + timedelta(days=2), "status", "To Do", "Closed", t["reporter"]))
    d["resolution"] = "Duplicate"
    dups.append(d)
issue_rows += dups

for t in issue_rows:
    if t["status"] == "Blocked" or (t["dep"] and R.random() < 0.6):
        n = R.randint(1, 3)
        for k in range(n):
            ts = t["created"] + timedelta(days=R.uniform(1, 20))
            if ts <= TODAY:
                comments.append((t["id"], ts, t["assignee"] or "unassigned",
                                 R.choice(TICKET_COMMENTS["blocked"]).format(d=t["dep"] or "client input")))
    if R.random() < 0.35:
        ts = t["created"] + timedelta(days=R.uniform(0.5, 10))
        if ts <= TODAY:
            comments.append((t["id"], ts, t["assignee"] or t["reporter"],
                             R.choice(TICKET_COMMENTS["normal"]).format(p=(t["reporter"] or "team").split()[0])))

issues_out = []
for t in issue_rows:
    st = last_status.get(t["id"], "To Do")
    res = t.get("resolution") or ("Done" if st == "Done" else ("Won't Do" if st == "Won't Do" else None))
    rdate = done_at.get(t["id"])
    if st == "Done" and R.random() < 0.04: rdate = None  # missing resolution date
    issues_out.append(dict(issue_key=key_of[t["id"]], project_key=key_of[t["id"]].split("-")[0], issue_type=t["type"],
                           summary=t["summary"], status=st, priority=t["priority"], assignee=t["assignee"],
                           reporter=t["reporter"], story_points=t["points"], sprint=t["sprint"],
                           component=t["component"], labels=";".join(l for l in t["labels"] if l),
                           created=fmt_ts(t["created"]), resolution=res,
                           resolved=fmt_ts(rdate) if rdate else None))
I = pd.DataFrame(issues_out)
CL = pd.DataFrame([dict(issue_key=key_of[e[0]], changed_at=fmt_ts(e[1]), field=e[2], from_value=e[3], to_value=e[4], author=e[5])
                   for e in sorted(events, key=lambda e: e[1]) if e[0] in key_of])
CM = pd.DataFrame([dict(issue_key=key_of[c[0]], created=fmt_ts(c[1]), author=c[2], body=c[3])
                   for c in sorted(comments, key=lambda c: c[1]) if c[0] in key_of])
SP = pd.DataFrame(sprint_rows)
SP = SP[pd.to_datetime(SP.start_date) <= TODAY]

# ----------------------------------------------------------------------------------
# 4. Outcomes for historical projects (the labels for "predict from similar past projects")
# ----------------------------------------------------------------------------------
outc = []
for p in P[P.state == "Closed"].itertuples():
    h = hcurve[p.project_id]
    tail = float(np.mean(h[int(len(h) * 0.6):]))
    late = max(0, round((0.72 - float(np.mean(h))) * 22 + NP.normal(0, 1)))
    outc.append(dict(project_id=p.project_id, actual_end_date=(datetime.fromisoformat(p.planned_end_date) + timedelta(weeks=late)).date().isoformat(),
                     weeks_late=late, over_budget_pct=max(0, round((0.75 - float(np.mean(h))) * 80 + NP.normal(0, 5))),
                     escalated=bool(h.min() < 0.3), client_csat=int(clip(round(1 + 4 * tail + NP.normal(0, 0.4)), 1, 5)),
                     final_outcome="On time" if late <= 1 else ("Late" if late <= 5 else "Severely late")))
OUTC = pd.DataFrame(outc)

# ----------------------------------------------------------------------------------
# 5. Meetings: Hinglish standups + i360 reviews with screen frames
# ----------------------------------------------------------------------------------
def en_pair(n):
    if n < 20: return EN_ONES[n]
    return EN_TENS[n // 10] + ("" if n % 10 == 0 else " " + EN_ONES[n % 10])


def spoken_number(n, style):
    a, b = divmod(n, 100)
    if style == "digits": return " ".join(EN_ONES[int(c)] for c in str(n))
    if style == "en_pairs":
        if n % 1000 == 0: return EN_ONES[n // 1000] + " thousand"
        return en_pair(a) + (" hundred" if b == 0 else " " + (("oh " + EN_ONES[b]) if b < 10 else en_pair(b)))
    if style == "hi_pairs":
        if n % 1000 == 0: return HINDI_NUM[n // 1000] + " hazaar"
        if b == 0: return HINDI_NUM[a] + " sau"
        return HINDI_NUM[a] + " " + HINDI_NUM[b]
    return str(n)


def spoken_key(key, allow_prefix=True):
    proj, num = key.split("-")
    style = R.choices(["en_pairs", "digits", "hi_pairs", "numeral"], [0.4, 0.15, 0.25, 0.2])[0]
    sn = spoken_number(int(num), style)
    pre = R.choice([proj + " ", "ticket ", "", "", proj + " "]) if allow_prefix else ""
    return f"{pre}{sn}".strip()


def val(x):
    return None if (x is None or (isinstance(x, float) and math.isnan(x))) else x


def first(n): return (val(n) or "team").split()[0]


def asr_noise(text, deva):
    toks = text.split(" ")
    out = []
    for w in toks:
        core = w.strip(",.?!—")
        if R.random() < 0.02: continue
        if core in ASR_CONFUSIONS and R.random() < 0.3:
            w = w.replace(core, R.choice(ASR_CONFUSIONS[core]))
        elif core in EN_ONES + EN_TENS and R.random() < 0.25:
            w = w.replace(core, str(EN_ONES.index(core)) if core in EN_ONES else str(EN_TENS.index(core) * 10))
        elif deva and core.lower() in DEVANAGARI:
            w = w.replace(core, DEVANAGARI[core.lower()])
        out.append(w)
    s = " ".join(out)
    for proj in jkey.values():
        if proj in s and R.random() < 0.3:
            s = s.replace(proj, R.choice([" ".join(proj), proj.lower(), proj.capitalize()]), 1)
    return s


OCR_SWAP = {"0": "O", "O": "0", "1": "l", "5": "S", "8": "B", "S": "5", "l": "1"}


def ocr_noise(s):
    return "".join(OCR_SWAP[c] if c in OCR_SWAP and R.random() < 0.04 else c for c in s)


meetings, segs, gold_segs, frames, decisions = [], [], [], [], []
ISS = {r.issue_key: r for r in I.itertuples()}


def ticket_state_at(key, when):
    st = "To Do"
    for e in CL_by_key.get(key, []):
        if e[0] <= when and e[1] in ("status", "created"):
            st = e[2]
    return st


CL_by_key = defaultdict(list)
for e in sorted(events, key=lambda e: e[1]):
    if e[0] in key_of:
        CL_by_key[key_of[e[0]]].append((e[1], e[2], e[4]))
open_keys_by_sprint = defaultdict(list)
for t in issue_rows:
    if t["id"] in key_of and t.get("resolution") != "Duplicate":
        for sp_ in t.get("sprints", [t["sprint"]]):
            open_keys_by_sprint[sp_].append(key_of[t["id"]])


class Meeting:
    def __init__(self, mid, kind, pid, when, title):
        self.mid, self.kind, self.pid, self.when = mid, kind, pid, when
        self.t = 0.0
        self.seg_i = 0
        self.screen = []  # (t0, t1, screen_type, payload)
        self.deva = R.random() < 0.4
        meetings.append(dict(meeting_id=mid, meeting_type=kind, project_id=pid, start_time=when.isoformat(timespec="minutes"),
                             title=title, source=R.choice(["Teams recording", "Fellow", "Teams recording"]),
                             asr_output_script="Devanagari+Latin" if self.deva else "Latin (romanized)"))

    def say(self, speaker, text, topic, mentioned=(), screen_mode=None, decision=None, project_topic=None):
        dur = max(2.0, len(text.split()) / R.uniform(2.2, 3.0))
        t0, t1 = self.t, self.t + dur
        sid = f"{self.mid}-{self.seg_i:03d}"
        segs.append(dict(meeting_id=self.mid, segment_id=sid, start_s=round(t0, 1), end_s=round(t1, 1),
                         speaker=speaker if R.random() > 0.05 else "SPEAKER_?", asr_text=asr_noise(text, self.deva)))
        gold_segs.append(dict(segment_id=sid, meeting_id=self.mid, spoken_text_true=text, topic=topic or "",
                              mentioned_keys=";".join(mentioned), screen_mode=screen_mode or ""))
        if decision:
            decisions.append(dict(meeting_id=self.mid, segment_id=sid, speaker=speaker, evidence_quote=text, **decision))
        self.seg_i += 1
        self.t = t1 + R.uniform(0.3, 1.5)
        return t0, t1

    def show(self, t0, t1, stype, payload):
        self.screen.append((t0, t1, stype, payload))

    def flush_frames(self):
        end = self.t
        t = 0.0
        while t <= end:
            cur = None
            for a, b, st, pl in self.screen:
                if a <= t < b: cur = (st, pl)
            st, pl = cur if cur else ("none", None)
            frames.append(dict(meeting_id=self.mid, t_s=round(t, 1), frame_file=f"{self.mid}/f_{int(t):05d}.png",
                               screen_type=st, ocr_text=ocr_noise(render(st, pl, self.when)) if pl else "",
                               gold_visible_keys=";".join(pl["keys"]) if pl else ""))
            t += 5.0


def render(st, pl, when=None):
    if st == "jira_ticket":
        k = pl["keys"][0]
        r = ISS[k]
        stt = ticket_state_at(k, when) if when else r.status
        return f"{k}  {r.summary}\nStatus: {stt.upper()}  Assignee: {val(r.assignee) or 'Unassigned'}  Priority: {r.priority}\n{r.sprint}"
    if st == "jira_board":
        return f"{pl['board']} | TO DO   IN PROGRESS   IN REVIEW   DONE\n" + "\n".join(f"{k} {ISS[k].summary[:28]}" for k in pl["keys"])
    if st == "i360_project":
        return f"i360  Project: {pl['name']}  Client: {pl['client']}\nStatus: {pl['status']}  Delivery Lead: {pl['lead']}"
    if st == "i360_portfolio":
        return "i360 Portfolio  |  " + "  |  ".join(f"{n}: {s}" for n, s in pl["rows"])
    return ""


def topic_screen(m, keys_in_order, idx, t0, t1, mode, board):
    key = keys_in_order[idx]
    prev_k = keys_in_order[idx - 1] if idx > 0 else None
    nxt = keys_in_order[idx + 1] if idx + 1 < len(keys_in_order) else None
    tk = lambda k: {"keys": [k]}
    if mode == "aligned":
        m.show(t0 - 1, t1 + 0.5, "jira_ticket", tk(key))
    elif mode == "screen_lag" and prev_k:
        lag = R.uniform(10, 35)
        m.show(t0 - 1, t0 + lag, "jira_ticket", tk(prev_k))
        m.show(t0 + lag, t1 + 0.5, "jira_ticket", tk(key))
    elif mode == "screen_ahead" and nxt:
        early = min(R.uniform(5, 18), (t1 - t0) * 0.6)
        m.show(t0 - 1, t1 - early, "jira_ticket", tk(key))
        m.show(t1 - early, t1 + 0.5, "jira_ticket", tk(nxt))
    elif mode == "board_view":
        m.show(t0 - 1, t1 + 0.5, "jira_board", {"keys": board, "board": board[0].split("-")[0] + " board"})
    elif mode == "divergent":
        other = R.choice([k for k in board if k != key] or [key])
        m.show(t0 - 1, t1 + 0.5, "jira_ticket", tk(other))
    else:
        m.show(t0 - 1, t1 + 0.5, "jira_ticket", tk(key))


def standup(p, when, mid):
    sid = SP[(SP.project_id == p.project_id) & (pd.to_datetime(SP.start_date) <= when)].sprint_id.iloc[-1]
    keys = [k for k in open_keys_by_sprint[sid] if ticket_state_at(k, when) not in ("Done", "Won't Do", "To Do", "Closed")]
    if len(keys) < 2:
        keys = [k for k in open_keys_by_sprint[sid] if ticket_state_at(k, when) not in ("Done", "Won't Do", "Closed")]
    if not keys: return
    R.shuffle(keys)
    topics = keys[:R.randint(3, min(6, max(3, len(keys))))]
    board = (topics + [k for k in open_keys_by_sprint[sid] if k not in topics])[:8]
    m = Meeting(mid, "Daily standup", p.project_id, when, f"{p.jira_key} standup")
    lead, team = first(p.delivery_lead), TEAM[p.project_id]
    m.say(p.delivery_lead, R.choice(["Okay sab log aa gaye? Chalo shuru karte hain.", "Good morning everyone, let's start.",
                                     "Screen share kar raha hoon, ek second.", "Sab audible ho? Okay, start karte hain."]), None)
    h = hcurve[p.project_id][min(len(hcurve[p.project_id]) - 1, (when - datetime.fromisoformat(p.start_date)).days // 7)]
    for idx, key in enumerate(topics):
        r = ISS[key]
        st = ticket_state_at(key, when)
        who = val(r.assignee) or R.choice(team)
        mode = R.choices(["aligned", "screen_lag", "screen_ahead", "board_view", "divergent"], [0.45, 0.2, 0.1, 0.1, 0.15])[0]
        tmpl = next((x for x in TICKET_TEMPLATES if x[0] == r.summary.rstrip(" (copy)- dup")), (r.summary, r.summary.lower(), []))
        short = tmpl[1]
        T0 = m.t
        if R.random() < 0.7:
            sk = spoken_key(key)
            intro = R.choice([f"Okay, next {sk} dekhte hain, {short} wala.", f"{sk} pe aate hain. {first(who)}, update do.",
                              f"Chalo, {sk}. Ye {short} wala ticket hai.", f"Let's pick up {sk}, the {short} one."])
            m.say(p.delivery_lead, intro, key, [key], mode)
        else:
            intro = R.choice([f"{first(who)}, woh {short} wala issue, uska kya hua?", f"Aur {short} ka kya status hai?",
                              f"{first(who)}, tumhara {short} wala kaam kahan tak pahuncha?"])
            m.say(p.delivery_lead, intro, key, [], mode)
        if st == "Blocked":
            dep = R.choice(DEPENDENCIES)
            m.say(who, R.choice([f"Isme blocker hai, client ne abhi tak {dep} nahi bheja.",
                                 f"Yahan hum stuck hain, {dep} ka wait kar rahe hain teen din se.",
                                 f"Still blocked on {dep}. Maine kal phir follow up kiya tha."]), key, [], mode)
        elif st in ("In Review", "QA"):
            m.say(who, R.choice(["Development complete hai, abhi code review mein hai.", "QA mein hai, kal tak sign-off aa jayega.",
                                 "PR raise kar diya hai, bas review pending hai."]), key, [], mode)
        else:
            m.say(who, R.choice([f"Haan, isme kaam chal raha hai, around {R.choice([40, 50, 60, 70])} percent done hai.",
                                 "Main kal se ispe hi hoon, aaj shaam tak PR raise kar dunga.",
                                 "It's in progress, QA ko kal handover karenge.",
                                 "Thoda complex nikla, estimate se zyada time lag raha hai."]), key, [], mode)
        if R.random() < 0.18:
            others = [k for k in board if k != key]
            if others:
                ok = R.choice(others)
                m.say(who, f"Ye {spoken_key(ok)} se bhi related hai, wahan bhi same issue aaya tha.", key, [ok], mode)
        if R.random() < (1 - h) * 0.8:
            m.say(R.choice([who, p.delivery_lead]), R.choice(["Mujhe lagta hai is sprint mein ye complete nahi hoga.",
                                                               "Timeline thoda risky lag raha hai.",
                                                               "Client demo se pehle ye ready hona chahiye, warna problem hogi."]), key, [], mode)
        r_dec = R.random()
        if r_dec < 0.6:
            if st == "Blocked":
                opt = R.choice([("status_change", "Blocked", "Isko Blocked mein daal do, aur client ko mail karo."),
                                ("priority_change", "High", "Iski priority High kar do, client ne escalate kiya hai."),
                                ("add_comment", "Waiting on client dependency", "Ticket pe comment daal do ki client dependency pending hai.")])
            elif st in ("In Review", "QA"):
                opt = R.choice([("status_change", "Done", "Theek hai, sign-off aate hi isko Done mark kar do."),
                                ("status_change", "Done", "Okay, isko Done kar do, QA ne pass kar diya.")])
            else:
                nf = R.choice([x for x in team if x != who] or team)
                opt = R.choice([("move_sprint", "next sprint", "Decision ye hai ki isko next sprint mein move karte hain."),
                                ("reassign", nf, f"{first(nf)}, tum isko le lo, {first(who)} ke paas bandwidth nahi hai."),
                                ("due_date", "Friday", "Iski due date Friday rakh do."),
                                ("priority_change", "High", "Iski priority High kar do.")])
            m.say(p.delivery_lead, opt[2], key, [], mode,
                  decision=dict(target_system="Jira", target_key=key, action=opt[0], new_value=opt[1], is_tentative=False))
        elif r_dec < 0.75:
            m.say(p.delivery_lead, R.choice(["Shayad isko next sprint mein le jaana padega, dekhte hain.",
                                             "Ho sakta hai priority badhani pade, kal decide karte hain."]), key, [], mode,
                  decision=dict(target_system="Jira", target_key=key, action="tentative", new_value="", is_tentative=True))
        topic_screen(m, topics, idx, T0, m.t, mode, board)
    m.say(p.delivery_lead, R.choice(["Okay, that's it for today. Thanks all.", "Theek hai, aaj ke liye itna hi. Thanks.",
                                     "Chalo, baaki offline discuss karte hain."]), None)
    m.flush_frames()


def i360_review(when, mid, live_projects):
    m = Meeting(mid, "i360 weekly review", None, when, "Weekly i360 portfolio review")
    pmo = "Kiran Bhatia (PMO)"
    rows = []
    for p in live_projects:
        wk = min(len(hcurve[p.project_id]) - 1, (when - datetime.fromisoformat(p.start_date)).days // 7)
        rows.append((p.project_name, typed_status_at[(p.project_id, wk)]))
    m.say(pmo, "Okay, i360 review shuru karte hain. Portfolio view share kar rahi hoon.", None)
    m.show(0, m.t + 2, "i360_portfolio", {"keys": [], "rows": rows})
    order = list(live_projects)
    for idx, p in enumerate(order):
        wk = min(len(hcurve[p.project_id]) - 1, (when - datetime.fromisoformat(p.start_date)).days // 7)
        typed = typed_status_at[(p.project_id, wk)]
        true = rag(hcurve[p.project_id][wk])
        lead = p.delivery_lead
        mode = R.choices(["aligned", "screen_lag", "divergent", "portfolio"], [0.5, 0.25, 0.15, 0.1])[0]
        T0 = m.t
        name_said = R.choice([p.project_name.split(" - ")[1], p.client, p.client.split()[0] + " wala project"])
        m.say(pmo, f"Next, {name_said}. {first(lead)}, status kya hai?", p.project_id, [], mode, project_topic=p.project_id)
        if typed == "Green":
            m.say(lead, R.choice(["Green hai, sab on track hai.", "Green, bas thoda QA delay hai, manageable hai.",
                                  "All good, client happy hai."]), p.project_id, [], mode)
        elif typed == "Yellow":
            m.say(lead, R.choice(["Yellow hai, client dependencies ki wajah se thoda delay hai.",
                                  "Amber rakha hai, velocity thodi kam hai is sprint."]), p.project_id, [], mode)
        else:
            m.say(lead, "Red hai. Release slip hoga, recovery plan bana rahe hain.", p.project_id, [], mode)
        if true != "Green" and typed == "Green":
            m.say(pmo, R.choice(["Lekin Jira mein blockers kaafi dikh rahe hain, aur velocity pichhle do sprint se gir rahi hai.",
                                 "But UAT dates already push ho chuki hain na?"]), p.project_id, [], mode)
            if R.random() < 0.5:
                m.say(lead, "Haan, par abhi green hi rakhte hain, next week dekhte hain. Client ko abhi escalate nahi karna.",
                      p.project_id, [], mode, decision=dict(target_system="i360", target_key=p.project_id, action="keep_status",
                                                            new_value="Green", is_tentative=False))
            else:
                m.say(pmo, "Theek hai, isko Yellow kar dete hain is week se.", p.project_id, [], mode,
                      decision=dict(target_system="i360", target_key=p.project_id, action="status_change",
                                    new_value="Yellow", is_tentative=False))
        pl = lambda q: {"keys": [], "name": q.project_name, "client": q.client, "lead": q.delivery_lead,
                        "status": typed_status_at[(q.project_id, min(len(hcurve[q.project_id]) - 1, (when - datetime.fromisoformat(q.start_date)).days // 7))]}
        if mode == "aligned" or (mode == "screen_lag" and idx == 0):
            m.show(T0 - 1, m.t + 0.5, "i360_project", pl(p))
        elif mode == "screen_lag":
            lag = R.uniform(8, 25)
            m.show(T0 - 1, T0 + lag, "i360_project", pl(order[idx - 1]))
            m.show(T0 + lag, m.t + 0.5, "i360_project", pl(p))
        elif mode == "divergent":
            m.show(T0 - 1, m.t + 0.5, "i360_project", pl(R.choice([q for q in order if q is not p])))
        else:
            m.show(T0 - 1, m.t + 0.5, "i360_portfolio", {"keys": [], "rows": rows})
    # project-level gold uses project_id in 'topic'; screen keys = project ids for i360 frames
    m.flush_frames()


def showcase_meeting(p, when):
    """Hand-scripted HMP standup: screen shows HMP-5500 while the team discusses HMP-4000."""
    mid = "MTG-DEMO-001"
    m = Meeting(mid, "Daily standup", p.project_id, when, "HMP standup (showcase)")
    m.deva = False
    L = p.delivery_lead
    team = TEAM[p.project_id]
    a4000 = val(ISS["HMP-4000"].assignee) or team[0]
    a5500 = val(ISS["HMP-5500"].assignee) or team[1]
    m.say(L, "Okay sab log aa gaye? Screen share kar raha hoon.", None)
    t0, _ = m.say(L, "Pehle HMP fifty five hundred dekhte hain, payment retry wala.", "HMP-5500", ["HMP-5500"], "aligned")
    m.say(a5500, "Haan, retry logic ho gaya hai, abhi unit tests likh raha hoon. Kal tak PR raise kar dunga.", "HMP-5500", [], "aligned")
    m.say(L, "Iski priority High kar do, client demo mein ye dikhana hai.", "HMP-5500", [], "aligned",
          decision=dict(target_system="Jira", target_key="HMP-5500", action="priority_change", new_value="High", is_tentative=False))
    t_sw, _ = m.say(L, f"Accha, {first(a4000)}, woh chaar hazaar wala, login timeout. Uska kya hua?", "HMP-4000", ["HMP-4000"], "divergent")
    m.say(a4000, "Abhi bhi blocked hai. Client ki IT team ne SSO config nahi bheja, teen hafte ho gaye.", "HMP-4000", [], "divergent")
    m.say(L, "Ye wahi issue hai jo fifty five hundred mein bhi aa sakta hai, payment bhi SSO session use karta hai.",
          "HMP-4000", ["HMP-5500"], "divergent")
    m.say(L, "Theek hai, isko Blocked hi rakho aur ticket pe comment daal do ki SSO config client se pending hai.", "HMP-4000", [], "divergent",
          decision=dict(target_system="Jira", target_key="HMP-4000", action="add_comment",
                        new_value="SSO config pending from client IT", is_tentative=False))
    m.say(L, "Aur iska owner ab main hoon, main client se baat karunga.", "HMP-4000", [], "divergent",
          decision=dict(target_system="Jira", target_key="HMP-4000", action="reassign", new_value=L, is_tentative=False))
    t_end4000 = m.t
    m.say(L, "Shayad isko next sprint mein le jaana padega, Friday tak dekhte hain.", "HMP-4000", [], "divergent",
          decision=dict(target_system="Jira", target_key="HMP-4000", action="tentative", new_value="", is_tentative=True))
    t_back = m.t
    m.say(L, "Okay, wapas fifty five hundred pe, test environment ready hai?", "HMP-5500", ["HMP-5500"], "aligned")
    m.say(a5500, "Haan, staging ready hai.", "HMP-5500", [], "aligned")
    m.say(L, "Theek hai, aaj ke liye itna hi. Thanks.", None)
    # screen stays on HMP-5500 for the whole meeting - the exact case Sandeep described
    m.show(t0 - 1, m.t + 1, "jira_ticket", {"keys": ["HMP-5500"]})
    m.flush_frames()


live = list(P[P.state == "Active"].itertuples())
mcount = 0
for wk in range(3, 0, -1):
    base = monday(TODAY) - timedelta(weeks=wk - 1)
    for p in live:
        for dd in (0, 3):
            when = base + timedelta(days=dd, hours=1, minutes=R.choice([0, 0, 15, 30]))
            if when > TODAY: continue
            mcount += 1
            standup(p, when, f"MTG-{mcount:04d}")
    when = base + timedelta(days=1, hours=6)
    if when <= TODAY:
        mcount += 1
        i360_review(when, f"MTG-{mcount:04d}", live)
showcase_meeting(live[0], monday(TODAY) + timedelta(days=3, hours=1, minutes=30))

# ----------------------------------------------------------------------------------
# 6. Write files
# ----------------------------------------------------------------------------------
w = lambda df, name: df.to_csv(os.path.join(OUT, name), index=False)
w(P.drop(columns=[]), "i360_projects.csv")
w(S, "i360_status_entries.csv")
w(SP, "jira_sprints.csv")
w(I, "jira_issues.csv")
w(CL, "jira_changelog.csv")
w(CM, "jira_comments.csv")
w(OUTC, "project_outcomes.csv")
w(pd.DataFrame(meetings), "meetings.csv")
w(pd.DataFrame(segs), "transcript_segments.csv")
w(pd.DataFrame(frames), "screen_frames.csv")
w(pd.DataFrame(gold_segs), "gold/transcript_gold.csv")
w(pd.DataFrame(decisions), "gold/decisions_gold.csv")
w(H, "hidden/true_health_weekly.csv")
w(HM, "hidden/project_scenarios.csv")
summary = {name: len(pd.read_csv(os.path.join(OUT, name))) for name in
           ["i360_projects.csv", "i360_status_entries.csv", "jira_sprints.csv", "jira_issues.csv", "jira_changelog.csv",
            "jira_comments.csv", "project_outcomes.csv", "meetings.csv", "transcript_segments.csv", "screen_frames.csv",
            "gold/transcript_gold.csv", "gold/decisions_gold.csv", "hidden/true_health_weekly.csv", "hidden/project_scenarios.csv"]}
print(json.dumps(summary, indent=1))
