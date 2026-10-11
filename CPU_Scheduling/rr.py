# Round Robin CPU Scheduling

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


# simulate() runs the Round Robin algorithm.
#   processes     = list of dicts like {"pid":"P1", "at":0, "bt":5}
#   time_quantum  = how many ticks each process runs before it is rotated
def simulate(processes, time_quantum=None):

    n = len(processes)

    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]

    # default time quantum is 2 (same rule as the old script)
    tq = time_quantum
    if tq is None or tq <= 0:
        tq = 2

    remaining = bt.copy()

    st = [-1] * n
    ct = [0] * n
    tat = [0] * n
    wt = [0] * n
    rt = [0] * n

    done = [0] * n
    run = {}            # time -> pid on CPU

    queue = []          # ready queue (holds process indexes)
    time = 0
    count = 0

    while count < n:

        # add any processes that have arrived and are not queued yet
        for i in range(n):
            if at[i] <= time and done[i] == 0 and i not in queue:
                if remaining[i] > 0:
                    queue.append(i)

        # nobody ready -> CPU idle one tick
        if len(queue) == 0:
            time = time + 1
            continue

        # take the process at the front of the queue
        current = queue.pop(0)

        if st[current] == -1:
            st[current] = time
            rt[current] = st[current] - at[current]

        # run it for up to tq ticks (or until it finishes)
        runc = 0
        while runc < tq and remaining[current] > 0:

            run[time] = pid[current]        # record this CPU tick
            remaining[current] = remaining[current] - 1
            time = time + 1
            runc = runc + 1

            # new arrivals during this slice join the queue
            for i in range(n):
                if at[i] <= time and done[i] == 0 and i != current:
                    if remaining[i] > 0 and i not in queue:
                        queue.append(i)

        if remaining[current] == 0:
            # finished
            ct[current] = time
            tat[current] = ct[current] - at[current]
            wt[current] = tat[current] - bt[current]
            done[current] = 1
            count = count + 1
        else:
            # still work left -> go to the back of the queue
            queue.append(current)

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

    tq_in = int(input("\nEnter Time Quantum (Enter 2 for default): "))
    data = simulate(procs, tq_in)

    print("\nPID\tCT\tTAT\tWT\tRT")
    for row in data["per_process"]:
        print(row["pid"], "\t", row["ct"], "\t", row["tat"],
              "\t", row["wt"], "\t", row["rt"])

    m = data["metrics"]
    print("\nAverage CT  =", m["avg_ct"])
    print("Average TAT =", m["avg_tat"])
    print("Average WT  =", m["avg_wt"])
    print("Average RT  =", m["avg_rt"])
