# insights.py
# Splits a run into steps and writes one explanation line per step.
#
# A "step" is one whole CPU allocation, not one tick:
#   FCFS / SJF      - the process keeps the CPU until it blocks or finishes
#   Round Robin     - one time quantum, or less if the process finishes
#   SRTF            - one tick, because it can be preempted at any tick
#
# Two sources of wording:
#   1. local   - worked out from the snapshots, always available
#   2. Groq AI - nicer sentences, fetched in a background thread

import json
import os
import threading
import urllib.error
import urllib.request

MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq sits behind Cloudflare, which rejects the default "Python-urllib"
# user agent with HTTP 403 (error 1010), so we must send our own.
USER_AGENT = "OS-Project-Scheduler/1.0"

TIMEOUT = 10        # seconds to wait for the API before giving up
MAX_AI_STEPS = 30   # steps sent to the API; longer runs use local lines

# The free tier on this account allows only 1000 output tokens per minute, and
# Groq refuses the request outright when max_tokens is above that.  Ask for
# roughly what the answer needs and never go near the ceiling.
OUT_TOKEN_CAP = 900

# how the algorithm picks the next process, used in the "starts" sentence
PICK_REASON = {
    "FCFS": "earliest arrival",
    "SJF": "shortest burst time",
    "SRTF": "shortest remaining time",
    "Round Robin": "front of the ready queue",
}


def build_steps(result, algo, tq=None): #
    """
    Cut the tick timeline into steps and return a list of (start, end) tick
    numbers, end excluded.  Together the steps cover the whole run.
    """
    snaps = result["snapshots"]
    if not snaps:
        return []

    # SRTF can switch at any tick, so every tick is its own step
    if algo == "SRTF":
        return [(i, i + 1) for i in range(len(snaps))]

    # join neighbouring ticks that are on the same process (or both idle)
    blocks = []
    for i, s in enumerate(snaps):
        pid = s["running"]
        if blocks and blocks[-1][2] == pid and blocks[-1][1] == i:
            blocks[-1][1] = i + 1
        else:
            blocks.append([i, i + 1, pid])

    # Round Robin: a process may hold the CPU for several quanta in a row when
    # nobody else is ready, so cut those blocks into quantum sized steps
    if algo == "Round Robin" and tq:
        out = []
        for start, end, pid in blocks:
            if pid is None:
                out.append((start, end))
                continue
            x = start
            while x < end:
                out.append((x, min(x + tq, end)))
                x = x + tq
        return out

    return [(b[0], b[1]) for b in blocks]


# =========================================================================
# Local lines, worked out from the snapshots
# =========================================================================

def _tables(procs, result):
    """The lookup tables the sentences need."""
    snaps = result["snapshots"]

    bt = {}
    for p in procs:
        bt[p["pid"]] = p["bt"]

    ct = {}
    tat = {}
    wt = {}
    for row in result.get("per_process", []):
        ct[row["pid"]] = row["ct"]
        tat[row["pid"]] = row["tat"]
        wt[row["pid"]] = row["wt"]

    # burst still left at the START of every tick
    remaining = []
    left = dict(bt)
    for s in snaps:
        remaining.append(dict(left))
        pid = s["running"]
        if pid is not None:
            left[pid] = left[pid] - 1

    return bt, ct, tat, wt, remaining


def build_local(procs, result, algo, tq=None, steps=None):
    """One sentence per step, derived from the snapshots."""
    snaps = result["snapshots"]
    if steps is None:
        steps = build_steps(result, algo, tq)

    bt, ct, tat, wt, remaining = _tables(procs, result)
    reason = PICK_REASON.get(algo, "the scheduling rule")

    # first tick each process reached the CPU
    first_run = {}
    for i, s in enumerate(snaps):
        pid = s["running"]
        if pid is not None and pid not in first_run:
            first_run[pid] = i

    lines = []
    for n, (a, b) in enumerate(steps):
        run = snaps[a]["running"]
        prev = snaps[a - 1]["running"] if a > 0 else None
        before_blocked = snaps[a - 1]["blocked"] if a > 0 else []
        now_blocked = snaps[b - 1]["blocked"]

        parts = []

        # --- arrivals inside this step ---
        arrived = [p["pid"] for p in procs if a <= p["at"] < b]
        if arrived:
            parts.append("%s arrives" % ", ".join(arrived))

        # --- what the CPU did ---
        if run is None:
            if now_blocked:
                parts.append("CPU idle t=%d to %d, every arrived process is on I/O"
                             % (a, b))
            elif any(p["at"] >= b for p in procs):
                parts.append("CPU idle t=%d to %d, nothing has arrived yet" % (a, b))
            else:
                parts.append("CPU idle t=%d to %d" % (a, b))
        else:
            span = "t=%d to %d" % (a, b)
            if first_run.get(run) == a:
                parts.append("%s starts %s, picked by %s (BT=%d)"
                             % (run, span, reason, bt[run]))
            elif prev is None:
                parts.append("%s resumes %s after the idle gap" % (run, span))
            elif prev != run:
                if ct.get(prev) == a:
                    parts.append("%s takes the CPU %s (%s), %s had finished"
                                 % (run, span, reason, prev))
                elif algo == "Round Robin":
                    parts.append("%s's quantum ran out, %s takes the CPU %s"
                                 % (prev, run, span))
                elif algo == "SRTF":
                    parts.append("%s preempts %s %s (remaining %d < %d)"
                                 % (run, prev, span,
                                    remaining[a][run], remaining[a][prev]))
                else:
                    parts.append("%s takes the CPU %s" % (run, span))
            else:
                parts.append("%s keeps the CPU %s" % (run, span))

            # --- how it ended ---
            left = remaining[a][run] - (b - a)
            if ct.get(run) == b:
                parts.append("completes at t=%d (TAT=%d, WT=%d)"
                             % (b, tat.get(run, 0), wt.get(run, 0)))
            elif algo == "Round Robin" and (b - a) == (tq or 2):
                parts.append("quantum used up, %d left, back of the queue" % left)
            elif left > 0 and run not in now_blocked:
                parts.append("%d unit%s left" % (left, "" if left == 1 else "s"))

        # --- I/O movement across this step ---
        for pid in now_blocked:
            if pid not in before_blocked:
                parts.append("%s blocks for I/O" % pid)
        for pid in before_blocked:
            if pid not in now_blocked and ct.get(pid) != a:
                parts.append("%s finishes I/O and is ready again" % pid)

        lines.append("; ".join(parts) + ".")

    return lines


# =========================================================================
# Groq AI lines
# =========================================================================

def _build_prompt(procs, result, algo, tq, with_io, steps):
    snaps = result["snapshots"]
    use = steps[:MAX_AI_STEPS]

    head = []
    for p in procs:
        if with_io:
            head.append("%s(AT=%d,BT=%d,IOat=%d,IOdur=%d)"
                        % (p["pid"], p["at"], p["bt"],
                           p.get("io_at", 0), p.get("io_dur", 0)))
        else:
            head.append("%s(AT=%d,BT=%d)" % (p["pid"], p["at"], p["bt"]))

    rows = []
    for n, (a, b) in enumerate(use):
        s = snaps[a]
        rows.append("step %d: t=%d..%d cpu=%s ready=%s blocked=%s"
                    % (n, a, b, s["running"] or "idle",
                       ",".join(s["ready"]) or "-",
                       ",".join(snaps[b - 1]["blocked"]) or "-"))

    done = []
    for r in result.get("per_process", []):
        done.append("%s(CT=%d,TAT=%d,WT=%d)" % (r["pid"], r["ct"], r["tat"], r["wt"]))

    quantum = "\nTime quantum: %d" % tq if tq else ""
    io_note = ("\nBlocked means the process is doing I/O, not using the CPU."
               if with_io else "")
    grain = ("Each step is one tick because SRTF can preempt at any tick."
             if algo == "SRTF" else
             "Each step is one whole CPU allocation covering t=start..end.")

    return (
        "You explain a CPU scheduling simulation to a student.\n\n"
        "Algorithm: %s%s%s\n"
        "Processes: %s\n"
        "Final figures: %s\n\n"
        "%s\n\nSteps:\n%s\n\n"
        "Write exactly %d insights, one for each step above, in order.\n"
        "Each insight is ONE sentence, at most 20 words, saying what the CPU did\n"
        "over that step and why the scheduler chose that process. Mention the time\n"
        "range. Use only the numbers given above; never invent or recompute values.\n"
        'Reply with JSON only: {"insights": ["step 0 line", "step 1 line", ...]}'
        % (algo, quantum, io_note, "; ".join(head), "; ".join(done) or "-",
           grain, "\n".join(rows), len(use))
    )


def _post(model, prompt, key, n_steps):
    """One Groq call.  Returns the list of strings, or None."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max(200, min(OUT_TOKEN_CAP, 80 + 30 * n_steps)),
        "response_format": {"type": "json_object"},
    }
    # gpt-oss thinks before answering and the thinking counts as output, so
    # keep it short or the reply runs into the token cap.
    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"

    req = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "User-Agent": USER_AGENT},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = json.loads(r.read().decode("utf-8"))

    choices = body.get("choices") or []
    if not choices:
        return None

    text = choices[0].get("message", {}).get("content") or ""
    parsed = json.loads(text)
    got = parsed.get("insights")
    if isinstance(got, list) and got:
        return [str(x).strip() for x in got]
    return None


def fetch_ai(procs, result, algo, tq, with_io, key, steps=None):
    """
    Ask Groq for the lines.
    Returns (lines, note); lines is None when every model failed and note
    says why, short enough to show under the log.
    """
    if not key:
        return None, "no API key"
    if steps is None:
        steps = build_steps(result, algo, tq)

    n = min(len(steps), MAX_AI_STEPS)
    prompt = _build_prompt(procs, result, algo, tq, with_io, steps)

    note = "no answer"
    for model in MODELS:
        try:
            lines = _post(model, prompt, key, n)
            if lines:
                return lines, ""
        except urllib.error.HTTPError as e:
            if e.code == 429:
                note = "rate limit reached"
            elif e.code in (401, 403):
                note = "API key rejected"
            else:
                note = "server error %d" % e.code
        except urllib.error.URLError:
            note = "no internet"
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            note = "bad reply"
    return None, note


# =========================================================================
# What the GUI calls
# =========================================================================

_cache = {}     # cache key -> finished AI lines


def _cache_key(procs, algo, tq, with_io):
    bits = [algo, str(tq), str(with_io)]
    for p in procs:
        bits.append("%s:%d:%d:%s:%s" % (p["pid"], p["at"], p["bt"],
                                        p.get("io_at", "-"), p.get("io_dur", "-")))
    return "|".join(bits)


def get_key():
    """Groq key from the environment, or None when it is not set up."""
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not key or key.startswith("your_"):
        return None
    return key


def build(procs, result, algo, tq=None, with_io=False, on_ai=None):
    """
    Return (steps, lines, pending).

    The local lines come back immediately.  If a Groq key is set and on_ai is
    given, a background thread fetches the AI lines and calls
    on_ai(lines, note): lines is None when it failed and note says why.
    That call happens on the worker thread, so the GUI must not touch any
    widget inside it.
    """
    steps = build_steps(result, algo, tq)
    local = build_local(procs, result, algo, tq, steps)
    key = get_key()

    if not key or on_ai is None:
        return steps, local, False

    ck = _cache_key(procs, algo, tq, with_io)
    if ck in _cache:
        return steps, _fit(_cache[ck], local), False

    def worker():
        lines, note = fetch_ai(procs, result, algo, tq, with_io, key, steps)
        if lines:
            _cache[ck] = lines
            on_ai(_fit(lines, local), "")
        else:
            on_ai(None, note)

    threading.Thread(target=worker, daemon=True).start()
    return steps, local, True


def _fit(ai_lines, local):
    """Make the AI list exactly as long as the run, padding from local."""
    out = list(ai_lines[:len(local)])
    while len(out) < len(local):
        out.append(local[len(out)])
    return out
