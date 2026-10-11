# Round Robin CPU Scheduling WITH I/O
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


# simulate() runs Round Robin with one I/O burst per process.
#   processes     = list of dicts like
#       {"pid":"P1", "at":0, "bt":5, "io_at":2, "io_dur":2}
#   time_quantum  = ticks each process runs before it is rotated
def simulate(processes, time_quantum=None):

    n = len(processes)

    pid = [p["pid"] for p in processes]
    at = [p["at"] for p in processes]
    bt = [p["bt"] for p in processes]
    io_at = [p["io_at"] for p in processes]
    io_dur = [p["io_dur"] for p in processes]

    tq = time_quantum
    if tq is None or tq <= 0:
        tq = 2

    bal = []
    for i in range(n):
        bal.append(bt[i] - io_at[i])

    first_remaining = io_at.copy()
    second_remaining = bal.copy()

    st = [-1] * n
    ct = [0] * n
    tat = [0] * n
    wt = [0] * n
    rt = [0] * n

    first_ct = [0] * n
    new_at = [0] * n
    new_bt = bal.copy()

    # state: 0 = waiting for first burst, 1 = doing I/O,
    #        2 = ready for second burst, 3 = finished
    state = [0] * n

    run = {}
    io = {}

    queue = []
    time = 0
    count = 0

    while count < n:

        # add processes ready for their first burst, or back from I/O
        for i in range(n):
            if state[i] == 0 and at[i] <= time and i not in queue:
                queue.append(i)
            elif state[i] == 2 and new_at[i] <= time and i not in queue:
                queue.append(i)

        # nobody ready -> CPU idle one tick
        if len(queue) == 0:
            time = time + 1
            continue

        current = queue.pop(0)

        if st[current] == -1:
            st[current] = time
            rt[current] = st[current] - at[current]

        runc = 0

        if state[current] == 0:

            # run up to tq ticks of the first burst
            while runc < tq and first_remaining[current] > 0:
                run[time] = pid[current]
                first_remaining[current] = first_remaining[current] - 1
                time = time + 1
                runc = runc + 1
                for i in range(n):
                    if state[i] == 0 and at[i] <= time and i != current:
                        if i not in queue:
                            queue.append(i)

            if first_remaining[current] == 0:
                # first burst done -> go to I/O
                first_ct[current] = time
                new_at[current] = first_ct[current] + io_dur[current]
                state[current] = 1
                for t in range(first_ct[current], new_at[current]):
                    if t not in io:
                        io[t] = []
                    io[t].append(pid[current])
            else:
                queue.append(current)

        else:

            # run up to tq ticks of the second burst
            while runc < tq and second_remaining[current] > 0:
                run[time] = pid[current]
                second_remaining[current] = second_remaining[current] - 1
                time = time + 1
                runc = runc + 1
                for i in range(n):
                    if state[i] == 0 and at[i] <= time and i != current:
                        if i not in queue:
                            queue.append(i)
                    if state[i] == 2 and new_at[i] <= time and i != current:
                        if i not in queue:
                            queue.append(i)

            if second_remaining[current] == 0:
                ct[current] = time
                tat[current] = ct[current] - at[current]
                wt[current] = tat[current] - bt[current]
                state[current] = 3
                count = count + 1
            else:
                queue.append(current)

        # move any process whose I/O has finished into the ready state
        for i in range(n):
            if state[i] == 1 and new_at[i] <= time:
                state[i] = 2

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

    tq_in = int(input("\nEnter Time Quantum: "))
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
