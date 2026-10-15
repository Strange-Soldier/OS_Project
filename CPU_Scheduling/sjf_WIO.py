# SJF CPU Scheduling WITH I/O (non-preemptive, shortest burst first)
# Each process runs a first CPU burst, then does I/O, then runs the rest.

# build_result() turns the raw run information into the dictionary the GUI
# wants.  It is the same helper used in every scheduling file.
def build_result(pids, at, bt, ct, tat, wt, rt, run, io):

    end_time = 0
    for pid in pids:
        if ct[pid] > end_time:
            end_time = ct[pid]

    timeline = []
    io_timeline = []
    for t in range(end_time):
        timeline.append(run.get(t, None))
        io_timeline.append(io.get(t, []))

    # Gantt chart: join neighbouring ticks of the same process
    gantt = []
    for t in range(end_time):
        pid = timeline[t]
        if pid is None:
            continue
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == t:
            gantt[-1][2] = t + 1
        else:
            gantt.append([pid, t, t + 1])
    gantt = [(g[0], g[1], g[2]) for g in gantt]

    # Snapshots: one picture of the system per tick
    snapshots = []
    for t in range(end_time):
        running = timeline[t]
        blocked = io_timeline[t]
        ready = []
        for pid in pids:
            if at[pid] <= t and ct[pid] > t:
                if pid != running and pid not in blocked:
                    ready.append(pid)
        if running is not None:
            event = running + " running"
        else:
            event = "CPU idle"
        snapshots.append({"t": t, "event": event, "running": running,
                          "ready": ready, "blocked": list(blocked)})

    # Context switches
    context_switches = 0
    last = None
    for seg in gantt:
        pid = seg[0]
        if last is not None and pid != last:
            context_switches = context_switches + 1
        last = pid

    # Average metrics
    n = len(pids)
    avg_wt = round(sum(wt[p] for p in pids) / n, 2)
    avg_tat = round(sum(tat[p] for p in pids) / n, 2)
    avg_rt = round(sum(rt[p] for p in pids) / n, 2)
    avg_ct = round(sum(ct[p] for p in pids) / n, 2)

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


# simulate() runs SJF with one I/O burst per process.
#   processes = list of dicts like
#       {"pid":"P1", "at":0, "bt":5, "io_at":2, "io_dur":2}
def simulate(processes, time_quantum=None):

    n = len(processes)

    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]
    io_at = [p["io_at"] for p in processes]
    io_dur = [p["io_dur"] for p in processes]

    # Per-process remaining work for each phase.
    rem1 = io_at.copy()                         # first CPU burst remaining
    rem2 = [bt[i] - io_at[i] for i in range(n)]  # second CPU burst remaining
    iorem = io_dur.copy()                       # I/O remaining

    ct = [0] * n
    tat = [0] * n
    wt = [0] * n
    rt = [-1] * n            # response time (-1 = not scheduled yet)

    arrived = [False] * n
    in_io = [False] * n
    done = [False] * n

    run = {}                 # time -> pid on CPU
    io = {}                  # time -> list of pids in I/O

    ready = []               # pool of (index, burst_number) ready to run
    cpu = None               # (index, burst_number) holding the CPU, or None

    def finish(i, end):
        ct[i] = end
        tat[i] = ct[i] - at[i]
        wt[i] = tat[i] - bt[i]
        done[i] = True

    # burst length a ready entry is about to run (used to pick the shortest)
    def burst_len(entry):
        i, bst = entry
        return rem1[i] if bst == 1 else rem2[i]

    time = 0
    count = 0
    guard = sum(bt) + sum(io_dur) + (max(at) if at else 0) + n + 5

    while count < n and time <= guard:

        # ---- 1) new arrivals join the ready pool for their first burst ----
        for i in range(n):
            if not arrived[i] and at[i] <= time:
                arrived[i] = True
                if rem1[i] > 0:
                    ready.append((i, 1))
                elif iorem[i] > 0:
                    in_io[i] = True
                elif rem2[i] > 0:
                    ready.append((i, 2))
                else:
                    finish(i, time); count += 1

        # ---- 2) dispatch SHORTEST available burst (non-preemptive) ----
        if cpu is None and ready:
            # pick the entry with the smallest burst; ties -> earliest arrival
            best = min(ready, key=lambda e: (burst_len(e), at[e[0]], e[0]))
            ready.remove(best)
            cpu = best
            ci = cpu[0]
            if rt[ci] == -1:
                rt[ci] = time - at[ci]

        # ---- 3) record what happens during THIS tick ----
        if cpu is not None:
            run[time] = pid[cpu[0]]
        for i in range(n):
            if in_io[i]:
                io.setdefault(time, []).append(pid[i])

        # ---- 4) advance the CPU burst by one tick ----
        if cpu is not None:
            ci, bst = cpu
            if bst == 1:
                rem1[ci] -= 1
            else:
                rem2[ci] -= 1

        # ---- 5) advance every active I/O by one tick, note completions ----
        io_finished = []
        for i in range(n):
            if in_io[i]:
                iorem[i] -= 1
                if iorem[i] == 0:
                    io_finished.append(i)

        # ---- 6) handle a CPU burst that just finished ----
        if cpu is not None:
            ci, bst = cpu
            if bst == 1 and rem1[ci] == 0:
                cpu = None
                if iorem[ci] > 0:
                    in_io[ci] = True
                elif rem2[ci] > 0:
                    ready.append((ci, 2))
                else:
                    finish(ci, time + 1); count += 1
            elif bst == 2 and rem2[ci] == 0:
                cpu = None
                finish(ci, time + 1); count += 1

        # ---- 7) processes whose I/O just finished become ready next tick ----
        for i in io_finished:
            in_io[i] = False
            if rem2[i] > 0:
                ready.append((i, 2))
            else:
                finish(i, time + 1); count += 1

        time = time + 1

    for i in range(n):
        if rt[i] == -1:
            rt[i] = 0

    at_d = {}; bt_d = {}; ct_d = {}; tat_d = {}; wt_d = {}; rt_d = {}
    for i in range(n):
        at_d[pid[i]] = at[i]; bt_d[pid[i]] = bt[i]; ct_d[pid[i]] = ct[i]
        tat_d[pid[i]] = tat[i]; wt_d[pid[i]] = wt[i]; rt_d[pid[i]] = rt[i]

    return build_result(pid, at_d, bt_d, ct_d, tat_d, wt_d, rt_d, run, io)


# Old interactive program kept for direct runs; skipped when imported.
if __name__ == "__main__":

    n = int(input("Enter number of processes: "))
    procs = []
    for i in range(n):
        print("\nEnter details for process", i + 1)
        pid_in = input("Enter PID: ")
        at_in = int(input("Enter Arrival Time: "))
        bt_in = int(input("Enter Burst Time: "))
        ioat_in = int(input("Enter I/O after CPU time: "))
        iodur_in = int(input("Enter I/O Duration: "))
        procs.append({"pid": pid_in, "at": at_in, "bt": bt_in,
                      "io_at": ioat_in, "io_dur": iodur_in})

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
