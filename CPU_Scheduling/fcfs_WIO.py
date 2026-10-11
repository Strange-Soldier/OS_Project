# FCFS CPU Scheduling WITH I/O
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


# simulate() runs FCFS with one I/O burst per process.
#   processes = list of dicts like
#       {"pid":"P1", "at":0, "bt":5, "io_at":2, "io_dur":2}
#   io_at  = how much CPU runs before the process goes to I/O
#   io_dur = how long the I/O takes
def simulate(processes, time_quantum=None):

    n = len(processes)

    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]
    io_at = [p["io_at"] for p in processes]
    io_dur = [p["io_dur"] for p in processes]

    # work left after the I/O (second CPU burst)
    bal = []
    for i in range(n):
        bal.append(bt[i] - io_at[i])

    st = [0] * n
    ct = [0] * n
    tat = [0] * n
    wt = [0] * n
    rt = [0] * n

    first_ct = [0] * n      # when the first CPU burst ends
    new_at = [0] * n        # when the process is ready again after I/O
    new_bt = bal.copy()     # size of the second CPU burst

    done_first = [0] * n    # finished first burst?
    done_second = [0] * n   # finished completely?

    run = {}                # time -> pid on CPU
    io = {}                 # time -> list of pids in I/O

    time = 0
    count = 0
    queue = []

    while count < n:

        # add newly arrived processes (still needing their first burst)
        for i in range(n):
            if done_first[i] == 0 and at[i] <= time and i not in queue:
                queue.append(i)

        # nobody ready -> CPU idle one tick
        if len(queue) == 0:
            time = time + 1
            continue

        current = queue.pop(0)

        st[current] = time
        rt[current] = st[current] - at[current]

        # --- first CPU burst: run io_at ticks ---
        for t in range(time, time + io_at[current]):
            run[t] = pid[current]
        time = time + io_at[current]

        first_ct[current] = time
        new_at[current] = first_ct[current] + io_dur[current]
        done_first[current] = 1

        # --- I/O: mark the process blocked during its I/O ---
        for t in range(first_ct[current], new_at[current]):
            if t not in io:
                io[t] = []
            io[t].append(pid[current])

        # jump forward to when I/O is finished
        time = new_at[current]

        # bring back processes whose I/O has finished
        for i in range(n):
            if done_first[i] == 1 and done_second[i] == 0:
                if new_at[i] <= time and i != current and i not in queue:
                    queue.append(i)

        # --- second CPU burst: run the remaining work ---
        for t in range(time, time + new_bt[current]):
            run[t] = pid[current]
        time = time + new_bt[current]

        ct[current] = time
        tat[current] = ct[current] - at[current]
        wt[current] = tat[current] - bt[current]

        done_second[current] = 1
        count = count + 1

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
