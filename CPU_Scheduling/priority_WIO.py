# Priority CPU Scheduling WITH I/O (non-preemptive, lower number = higher priority)
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


# simulate() runs non-preemptive Priority scheduling with one I/O burst.
#   processes = list of dicts like
#       {"pid":"P1", "at":0, "bt":5, "io_at":2, "io_dur":2, "priority":2}
#   (lower priority number means the process is more important)
def simulate(processes, time_quantum=None):

    n = len(processes)

    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]
    io_at = [p["io_at"] for p in processes]
    io_dur = [p["io_dur"] for p in processes]
    pr = [p["priority"] for p in processes]

    bal = []
    for i in range(n):
        bal.append(bt[i] - io_at[i])

    st = [0] * n
    ct = [0] * n
    tat = [0] * n
    wt = [0] * n
    rt = [0] * n

    first_ct = [0] * n
    new_at = [0] * n
    new_bt = bal.copy()

    done_first = [0] * n
    done_second = [0] * n

    run = {}
    io = {}

    time = 0
    count = 0

    while count < n:

        # 1) among arrived processes needing their first burst, pick best priority
        best = -1
        for i in range(n):
            if done_first[i] == 0 and at[i] <= time:
                if best == -1:
                    best = i
                elif pr[i] < pr[best]:
                    best = i

        # 2) if none, among processes back from I/O, pick best priority
        if best == -1:
            for i in range(n):
                if done_first[i] == 1 and done_second[i] == 0:
                    if new_at[i] <= time:
                        if best == -1:
                            best = i
                        elif pr[i] < pr[best]:
                            best = i

        # nobody ready -> CPU idle one tick
        if best == -1:
            time = time + 1
            continue

        if done_first[best] == 0:

            # --- first CPU burst ---
            st[best] = time
            rt[best] = st[best] - at[best]

            for t in range(time, time + io_at[best]):
                run[t] = pid[best]
            time = time + io_at[best]

            first_ct[best] = time
            new_at[best] = first_ct[best] + io_dur[best]
            done_first[best] = 1

            # --- I/O: process is blocked during its I/O ---
            for t in range(first_ct[best], new_at[best]):
                if t not in io:
                    io[t] = []
                io[t].append(pid[best])

        else:

            # --- second CPU burst ---
            for t in range(time, time + new_bt[best]):
                run[t] = pid[best]
            time = time + new_bt[best]

            ct[best] = time
            tat[best] = ct[best] - at[best]
            wt[best] = tat[best] - bt[best]

            done_second[best] = 1
            count = count + 1

    at_d = {}; bt_d = {}; ct_d = {}; tat_d = {}; wt_d = {}; rt_d = {}
    for i in range(n):
        at_d[pid[i]] = at[i]; bt_d[pid[i]] = bt[i]; ct_d[pid[i]] = ct[i]
        tat_d[pid[i]] = tat[i]; wt_d[pid[i]] = wt[i]; rt_d[pid[i]] = rt[i]

    return build_result(pid, at_d, bt_d, ct_d, tat_d, wt_d, rt_d, run, io)


# Simple interactive program for running the file directly; skipped on import.
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
        pr_in = int(input("Enter Priority (lower = higher priority): "))
        procs.append({"pid": pid_in, "at": at_in, "bt": bt_in,
                      "io_at": ioat_in, "io_dur": iodur_in, "priority": pr_in})

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
