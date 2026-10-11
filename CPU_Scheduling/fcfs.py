# FCFS (First Come First Serve) CPU Scheduling

# ---------------------------------------------------------------------------
# build_result() turns the raw run information into the dictionary the GUI
# wants.  It is the SAME in every scheduling file so each file stays complete
# and can be explained on its own.
#   pids   : list of process ids in display order (e.g. ["P1","P2","P3"])
#   at/ct/tat/wt/rt : dictionaries keyed by pid with each process's numbers
#   run    : dictionary  time -> pid that is using the CPU at that tick
#   io     : dictionary  time -> list of pids doing I/O at that tick
# ---------------------------------------------------------------------------
def build_result(pids, at, bt, ct, tat, wt, rt, run, io):

    # how many ticks long is the whole simulation
    end_time = 0
    for pid in pids:
        if ct[pid] > end_time:
            end_time = ct[pid]

    # turn the run/io dictionaries into simple lists, one slot per tick
    timeline = []          # timeline[t] = pid on CPU at tick t (or None)
    io_timeline = []       # io_timeline[t] = list of pids in I/O at tick t
    for t in range(end_time):
        timeline.append(run.get(t, None))
        io_timeline.append(io.get(t, []))

    # ---- Gantt chart: join neighbouring ticks of the same process ----
    gantt = []
    for t in range(end_time):
        pid = timeline[t]
        if pid is None:
            continue                       # CPU idle, no bar here
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == t:
            gantt[-1][2] = t + 1           # stretch the current bar
        else:
            gantt.append([pid, t, t + 1])  # begin a new bar
    gantt = [(g[0], g[1], g[2]) for g in gantt]   # make them tuples

    # ---- Snapshots: one picture of the system per tick ----
    snapshots = []
    for t in range(end_time):
        running = timeline[t]
        blocked = io_timeline[t]
        ready = []
        for pid in pids:
            # a process is "ready" if it has arrived, is not finished,
            # and is neither running nor doing I/O right now
            if at[pid] <= t and ct[pid] > t:
                if pid != running and pid not in blocked:
                    ready.append(pid)
        if running is not None:
            event = running + " running"
        else:
            event = "CPU idle"
        snapshots.append({"t": t, "event": event, "running": running,
                          "ready": ready, "blocked": list(blocked)})

    # ---- Context switches: how many times the CPU changed process ----
    context_switches = 0
    last = None
    for seg in gantt:
        pid = seg[0]
        if last is not None and pid != last:
            context_switches = context_switches + 1
        last = pid

    # ---- Average metrics ----
    n = len(pids)
    avg_wt = round(sum(wt[p] for p in pids) / n, 2)
    avg_tat = round(sum(tat[p] for p in pids) / n, 2)
    avg_rt = round(sum(rt[p] for p in pids) / n, 2)
    avg_ct = round(sum(ct[p] for p in pids) / n, 2)

    # CPU utilization = busy ticks / total ticks
    busy = 0
    for t in range(end_time):
        if timeline[t] is not None:
            busy = busy + 1
    if end_time > 0:
        cpu_util = round(busy / end_time * 100, 2)
    else:
        cpu_util = 0.0

    metrics = {"avg_wt": avg_wt, "avg_tat": avg_tat, "avg_rt": avg_rt,
               "avg_ct": avg_ct, "cpu_util": cpu_util,
               "context_switches": context_switches}

    per_process = []
    for pid in pids:
        per_process.append({"pid": pid, "ct": ct[pid], "tat": tat[pid],
                            "wt": wt[pid], "rt": rt[pid]})

    return {"snapshots": snapshots, "gantt": gantt,
            "metrics": metrics, "per_process": per_process}


# ---------------------------------------------------------------------------
# simulate() runs the FCFS algorithm.
#   processes = list of dicts like {"pid":"P1", "at":0, "bt":5}
# ---------------------------------------------------------------------------
def simulate(processes, time_quantum=None):

    n = len(processes)

    # pull the fields out into simple parallel lists (same as the old code)
    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]

    # sort by arrival time (smallest first) -- exactly like the old script
    for i in range(n):
        for j in range(i + 1, n):
            if at[i] > at[j]:
                at[i], at[j] = at[j], at[i]
                bt[i], bt[j] = bt[j], bt[i]
                pid[i], pid[j] = pid[j], pid[i]

    st = [0] * n        # start time
    ct = [0] * n        # completion time
    tat = [0] * n       # turnaround time
    wt = [0] * n        # waiting time
    rt = [0] * n        # response time

    run = {}            # time -> pid on CPU (filled while running)

    time = 0

    # run each process in arrival order, one after another
    for i in range(n):

        # if the CPU is idle waiting for the next arrival, jump time forward
        if time < at[i]:
            time = at[i]

        st[i] = time
        rt[i] = st[i] - at[i]

        # mark every tick this process uses the CPU
        for t in range(time, time + bt[i]):
            run[t] = pid[i]

        time = time + bt[i]

        ct[i] = time
        tat[i] = ct[i] - at[i]
        wt[i] = tat[i] - bt[i]

    # turn the parallel lists into dictionaries keyed by pid for build_result
    at_d = {}; bt_d = {}; ct_d = {}; tat_d = {}; wt_d = {}; rt_d = {}
    for i in range(n):
        at_d[pid[i]] = at[i]; bt_d[pid[i]] = bt[i]; ct_d[pid[i]] = ct[i]
        tat_d[pid[i]] = tat[i]; wt_d[pid[i]] = wt[i]; rt_d[pid[i]] = rt[i]

    return build_result(pid, at_d, bt_d, ct_d, tat_d, wt_d, rt_d, run, {})


# Old interactive program kept for direct runs; skipped when imported.
if __name__ == "__main__":

    n = int(input("Enter number of processes: "))
    procs = []
    for i in range(n):
        print("\nEnter details for process", i + 1)
        pid_in = input("Enter PID: ")
        at_in = int(input("Enter Arrival Time: "))
        bt_in = int(input("Enter Burst Time: "))
        procs.append({"pid": pid_in, "at": at_in, "bt": bt_in})

    data = simulate(procs)

    print("\nPID\tCT\tTAT\tWT\tRT")
    for row in data["per_process"]:
        print(row["pid"], "\t", row["ct"], "\t", row["tat"],
              "\t", row["wt"], "\t", row["rt"])

    m = data["metrics"]
    print("\nAverage CT  =", m["avg_ct"])
    print("Average TAT =", m["avg_tat"])
    print("Average WT  =", m["avg_wt"])
    print("Average RT  =", m["avg_rt"])
