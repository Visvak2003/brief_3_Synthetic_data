# Project Pulse: synthetic data pack (Brief 3)

All data here is **fictional**. It is shaped to look like Icreon's world, based on what we heard in our meetings:
i360 status entries, Jira sprints/issues/changelog, and Hindi-English meeting transcripts with screen frames.

## Run it
```
pip install pandas numpy
python generate.py                     # writes ./data (seed 42, 60 past + 8 live projects)
python generate.py --seed 7 --n_hist 150 --n_live 10 --out data_big
python topic_tracker.py data           # compares screen-only vs speech-only vs fused topic tracking
```

## The one rule that makes this data useful
Every project has a **hidden true health** curve (`hidden/true_health_weekly.csv`).
Jira signals and the typed i360 status are both *generated from* that hidden truth, with noise, delay and bias.
Our detector must never read `hidden/` or `gold/`. Those folders are only for scoring.
If the detector used the same rules as the generator, it would score 100% and prove nothing.

Project scenarios (hidden): healthy, slow_burn (scope creep, velocity slides), sudden_shock (key person leaves),
client_blocked (waiting on client inputs), recovering (goes bad, then recovers).

## Files
| File | What it imitates | Main columns |
|---|---|---|
| `i360_projects.csv` | i360 project register | project_id, project_name, client, jira_key, location, criticality, delivery_lead, team_size, start/planned_end, state |
| `i360_status_entries.csv` | weekly typed status | project_id, week_ending, typed_status, status_comment, entered_by, entered_at |
| `jira_sprints.csv` | sprints | sprint_id, project_id, start/end, goal, committed_points, completed_points_reported |
| `jira_issues.csv` | issues (current state) | issue_key, type, summary, status, priority, assignee, story_points, sprint, labels, created, resolved |
| `jira_changelog.csv` | issue history | issue_key, changed_at, field, from_value, to_value, author |
| `jira_comments.csv` | issue comments (some Hinglish) | issue_key, created, author, body |
| `project_outcomes.csv` | how past projects ended | weeks_late, over_budget_pct, escalated, client_csat, final_outcome |
| `meetings.csv` | Teams/Fellow recordings | meeting_id, type (standup / i360 review), project_id, start_time, asr_output_script |
| `transcript_segments.csv` | speech-to-text output (noisy) | segment_id, start_s, end_s, speaker, asr_text |
| `screen_frames.csv` | FFmpeg frame every 5 s + OCR | meeting_id, t_s, frame_file, screen_type, ocr_text |
| `gold/transcript_gold.csv` | answer key | true spoken text, topic (ticket or project), mentioned_keys, screen_mode |
| `gold/decisions_gold.csv` | answer key | decisions that should be posted to Jira / i360, with quotes; tentative ones flagged |
| `hidden/true_health_weekly.csv` | answer key | true_health_score (0-1), true_rag |
| `hidden/project_scenarios.csv` | answer key | scenario, onset week, block windows |

## Mess that is built in on purpose
Typed status lags reality by 1-3 weeks and leans green (some leads are more optimistic than others).
Weeks with no status entry, late entries, and values like `green`, `G` and `Amber`.
Locations written as `US` / `USA` / `United States`.
About 15% of stories have no story points, labels are inconsistent (`blocked`, `BLOCKER`, `waiting-on-client`), and about 3% of issues are duplicates.
Some issues are Done but have no resolution date, and about 5% of timestamps use Jira's export format (`16/Oct/26 3:45 PM`).
Ticket numbers jump (HMP goes from about 4100 to 5401 after a "board merge").
ASR output mixes Devanagari and Latin and spells ticket numbers as words (`fifty five hundred`, `chaar hazaar`, `baarah nawaasi`). It also mishears words (`stating` for staging) and sometimes labels the speaker as `SPEAKER_?`.
OCR swaps characters (`HMP-55OO`, `5tatus`).
Screen modes: aligned, screen_lag, screen_ahead, board_view, and divergent (the screen shows a different ticket from the one being discussed).

## Showcase meeting: `MTG-DEMO-001`
An HMP standup where the screen shows **HMP-5500** the whole time, while the team discusses **HMP-4000**
("chaar hazaar wala, login timeout"). It also includes a side-reference to 5500 that must NOT switch the topic,
two firm decisions on 4000, and one tentative remark that must NOT be posted.

## Ask Sandeep to sanity-check
Sprint length, team size, tickets per sprint, how often status is updated, how often projects go yellow or red,
how late typed status usually is, typical meeting length, how often people say ticket numbers out loud, and
what i360 fields really exist. Change the numbers in `generate.py` and `vocab.py`, then regenerate.
