"""
Baseline: "which ticket / project are they talking about right now?"
Compares 3 methods on the synthetic meetings and scores them against gold labels.

  A. screen_only  - trust whatever ticket/project the OCR sees on screen
  B. speech_only  - trust the last ticket/project said out loud
  C. fused        - speech outranks screen, keep a running "current topic",
                    match descriptions, ignore side-references, flag conflicts

Usage: python topic_tracker.py [data_dir]
"""
import difflib, re, sys
import pandas as pd

from vocab import EN_ONES, EN_TENS, HINDI_NUM, DEVANAGARI

D = sys.argv[1] if len(sys.argv) > 1 else "data"
seg = pd.read_csv(f"{D}/transcript_segments.csv")
frm = pd.read_csv(f"{D}/screen_frames.csv")
mtg = pd.read_csv(f"{D}/meetings.csv")
iss = pd.read_csv(f"{D}/jira_issues.csv")
prj = pd.read_csv(f"{D}/i360_projects.csv")
gold = pd.read_csv(f"{D}/gold/transcript_gold.csv")

# ---------------- spoken-number parser (English words, digits, Hindi words) ----------------
NUMW = {w: i for i, w in enumerate(EN_ONES)}
NUMW.update({w: i * 10 for i, w in enumerate(EN_TENS) if w != "_"})
for i, w in enumerate(HINDI_NUM):
    if w not in ("do", "saath", "shunya"):  # 'do' (= 2) and 'saath' (= 60) are also everyday words
        NUMW.setdefault(w, i)
MULT = {"hundred": 100, "sau": 100, "thousand": 1000, "hazaar": 1000, "hazar": 1000}


def numbers_in(text):
    toks = re.findall(r"[a-zA-Z]+|\d+", text.lower())
    runs, cur = [], []
    for t in toks:
        if t.isdigit() or t in NUMW or t in MULT or (t == "oh" and cur):
            cur.append(t)
        else:
            if cur: runs.append(cur)
            cur = []
    if cur: runs.append(cur)
    out = []
    for r in runs:
        chunks = []  # fold "fifty five" / "fifty 5" -> 55 ; apply hundred/thousand
        for t in r:
            if t in MULT:
                if chunks and isinstance(chunks[-1], int):
                    chunks[-1] = chunks[-1] * MULT[t]
                continue
            v = int(t) if t.isdigit() else (0 if t == "oh" else NUMW[t])
            if chunks and isinstance(chunks[-1], int) and chunks[-1] % 10 == 0 and 20 <= chunks[-1] <= 90 and 0 < v < 10:
                chunks[-1] += v
            else:
                chunks.append(v)
        s = "".join(str(c) for c in chunks)
        if s:
            out.append(int(s))
        if len(chunks) > 1:  # also allow sums like "four thousand" + "five hundred"
            out.append(sum(chunks))
    return out


def ocr_fix(s):
    """Fix common OCR confusions inside ticket keys: HMP-55OO -> HMP-5500"""
    def fix(m):
        num = m.group(2).translate(str.maketrans("OolISB", "001158"))
        return f"{m.group(1)}-{num}"
    return re.sub(r"\b([A-Z0-9]{2,6})-([0-9OolISB]{2,6})\b", fix, s or "")


SIDE = re.compile(r"\b(related|bhi|wahi|jaisa|similar|same issue)\b", re.I)
SHIFT = re.compile(r"\b(next|chalo|aate hain|pick up|wapas|let's|dekhte hain|aur)\b", re.I)
STOP = set("the a an for of to on in and with after when not page from new set up add".split())


def kw(s):
    return {w[:5] for w in re.findall(r"[a-z]{4,}", (s or "").lower()) if w not in STOP}


def deva_to_roman(s):
    inv = {v: k for k, v in DEVANAGARI.items()}
    return " ".join(inv.get(w, w) for w in s.split())


results = []
for m in mtg.itertuples():
    S = seg[seg.meeting_id == m.meeting_id].sort_values("start_s")
    F = frm[frm.meeting_id == m.meeting_id].sort_values("t_s")
    is_review = m.meeting_type.startswith("i360")
    if is_review:
        cands = {p.project_id: kw(p.project_name) | kw(p.client) for p in prj[prj.state == "Active"].itertuples()}
        name_of = {p.project_id: p.project_name.lower() for p in prj.itertuples()}
    else:
        key = prj.loc[prj.project_id == m.project_id, "jira_key"].iloc[0]
        open_iss = iss[(iss.project_key == key) & (~iss.status.isin(["Closed"]))]
        cands = {r.issue_key: kw(r.summary) for r in open_iss.itertuples()}
        num_to_key = {int(k.split("-")[1]): k for k in cands}
    cur_scr = cur_sp = cur_fu = None
    stale_screen = None  # screen key we stopped trusting because speech moved away from it
    prev_scr = None
    for s in S.itertuples():
        text = deva_to_roman(str(s.asr_text))
        mid_t = (s.start_s + s.end_s) / 2
        fr = F[F.t_s <= mid_t].tail(1)
        ocr = ocr_fix(str(fr.ocr_text.iloc[0])) if len(fr) and isinstance(fr.ocr_text.iloc[0], str) else ""
        # --- what's on screen
        if is_review:
            mm = re.search(r"Project:\s*(.+?)\s+Client:", ocr)
            hit = difflib.get_close_matches(mm.group(1).lower(), list(name_of.values()), n=1, cutoff=0.6) if mm else []
            scr_keys = [pid for pid, n in name_of.items() if hit and n == hit[0] and pid in cands]
        else:
            scr_keys = [k for k in re.findall(r"\b[A-Z]{2,6}-\d{2,6}\b", ocr) if k in cands]
        scr_single = scr_keys[0] if len(scr_keys) == 1 else None
        # --- what was said
        if is_review:
            words = kw(text)
            said = [pid for pid, k in cands.items() if len(words & k) >= 1 and re.search(r"status kya|next", text, re.I)]
        else:
            said = [num_to_key[n] for n in numbers_in(text) if n in num_to_key]
        side = bool(SIDE.search(text)) and cur_fu is not None
        shift = bool(SHIFT.search(text))
        # A. screen only
        cur_scr = scr_single or cur_scr
        # B. speech only
        if said: cur_sp = said[0]
        # C. fused scoring
        score = {c: 0.0 for c in cands}
        for c in said:
            score[c] += 0.8 if side else 3.0
        if not is_review:
            words = kw(text)
            for c, k in cands.items():
                ov = len(words & k)
                if ov: score[c] += min(ov, 2) * 1.2
        if cur_fu in score:
            score[cur_fu] += 0.5 if shift else 1.5
        if scr_single in score:
            score[scr_single] += 0.3 if scr_single == stale_screen else 1.0
            if scr_single != prev_scr and scr_single != stale_screen:
                score[scr_single] += 1.0  # presenter just changed the screen: a hint the topic moved
        prev_scr = scr_single or prev_scr
        best = max(score, key=score.get) if score else None
        top = sorted(score.values(), reverse=True)[:2] + [0, 0]
        explicit_switch = bool(said) and not side and best in said
        if best is not None and score[best] > 0:
            # hysteresis: only change topic on an explicit spoken switch or a clear margin
            if cur_fu is None or explicit_switch or score[best] - score.get(cur_fu, 0) >= 1.5:
                if scr_single and scr_single != best and explicit_switch:
                    stale_screen = scr_single  # speech moved on, screen did not
                cur_fu = best
        if scr_single and scr_single != stale_screen:
            stale_screen = None if scr_single == cur_fu else stale_screen
        conf = (top[0] - top[1]) / (top[0] + 1e-9) if top[0] else 0
        results.append(dict(meeting_id=m.meeting_id, segment_id=s.segment_id, review=is_review,
                            screen_only=cur_scr, speech_only=cur_sp, fused=cur_fu, fused_conf=round(conf, 2),
                            screen_disagrees=bool(scr_single and cur_fu and scr_single != cur_fu)))

Rz = pd.DataFrame(results).merge(gold[["segment_id", "topic", "screen_mode"]], on="segment_id")
Rz = Rz[Rz.topic.notna()]
print(f"Segments scored: {len(Rz)}  (chit-chat excluded)\n")
for label, sub in [("Standups (Jira tickets)", Rz[~Rz.review]), ("i360 reviews (projects)", Rz[Rz.review])]:
    print(label)
    for meth in ["screen_only", "speech_only", "fused"]:
        print(f"  {meth:12s} accuracy = {(sub[meth] == sub.topic).mean():.0%}")
    print("  accuracy by screen situation:")
    tab = sub.groupby("screen_mode").apply(lambda g: pd.Series({m: f"{(g[m] == g.topic).mean():.0%}" for m in
                                                                 ["screen_only", "speech_only", "fused"]} | {"n": len(g)}),
                                           include_groups=False)
    print(tab.to_string().replace("\n", "\n    "))
    print()
low = Rz[Rz.fused_conf < 0.3]
print(f"Fused: {len(low)} segments with low confidence (<0.3) -> route to human review; "
      f"accuracy on the rest = {(Rz[Rz.fused_conf >= 0.3].fused == Rz[Rz.fused_conf >= 0.3].topic).mean():.0%}")
demo = pd.DataFrame(results).merge(gold, on="segment_id")
demo = demo[demo.meeting_id_x == "MTG-DEMO-001"][["segment_id", "spoken_text_true", "topic", "screen_only", "fused", "screen_disagrees"]]
print("\nShowcase meeting (screen shows HMP-5500 all the time):")
print(demo.to_string(index=False, max_colwidth=70))
pd.DataFrame(results).to_csv(f"{D}/../topic_tracker_output.csv", index=False)
