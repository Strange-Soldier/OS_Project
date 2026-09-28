n = int(input("Enter number of processes: "))

pid = []
at = []
bt = []
io_at = []
io_dur = []

for i in range(n):
    print("\nEnter details for process", i + 1)
    pid.append(input("Enter PID: "))
    at.append(int(input("Enter Arrival Time: ")))
    bt.append(int(input("Enter Burst Time: ")))
    io_at.append(int(input("Enter I/O after CPU time: ")))
    io_dur.append(int(input("Enter I/O Duration: ")))

tq = int(input("\nEnter Time Quantum: "))

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

state = [0] * n

queue = []
time = 0
count = 0

print("\nExecution")

while count < n:

    for i in range(n):

        if state[i] == 0 and at[i] <= time and i not in queue:
            queue.append(i)

        elif state[i] == 2 and new_at[i] <= time and i not in queue:
            queue.append(i)

    if len(queue) == 0:
        time = time + 1
        continue

    current = queue.pop(0)

    if st[current] == -1:
        st[current] = time
        rt[current] = st[current] - at[current]

    run = 0

    if state[current] == 0:

        while run < tq and first_remaining[current] > 0:

            first_remaining[current] = first_remaining[current] - 1
            time = time + 1
            run = run + 1

            for i in range(n):
                if state[i] == 0 and at[i] <= time and i != current:
                    if i not in queue:
                        queue.append(i)

        print("\nTime =", time)
        print("Ready Queue:", end=" ")

        for i in queue:
            print(pid[i], end=" ")

        print()
        print("Running:", pid[current])
        print("Bal:", first_remaining[current])

        if first_remaining[current] == 0:

            first_ct[current] = time
            new_at[current] = first_ct[current] + io_dur[current]

            state[current] = 1

            print("I/O Queue:", pid[current])
            print("I/O Start:", first_ct[current])
            print("I/O End:", new_at[current])

        else:
            queue.append(current)

    else:

        while run < tq and second_remaining[current] > 0:

            second_remaining[current] = second_remaining[current] - 1
            time = time + 1
            run = run + 1

            for i in range(n):
                if state[i] == 0 and at[i] <= time and i != current:
                    if i not in queue:
                        queue.append(i)

                if state[i] == 2 and new_at[i] <= time and i != current:
                    if i not in queue:
                        queue.append(i)

        print("\nTime =", time)
        print("Ready Queue:", end=" ")

        for i in queue:
            print(pid[i], end=" ")

        print()
        print("Running:", pid[current])
        print("Bal:", second_remaining[current])

        if second_remaining[current] == 0:

            ct[current] = time
            tat[current] = ct[current] - at[current]
            wt[current] = tat[current] - bt[current]

            state[current] = 3
            count = count + 1

        else:
            queue.append(current)

    for i in range(n):
        if state[i] == 1 and new_at[i] <= time:
            state[i] = 2

print("\n")
print("PID\tAT\tBT\tI/Oat\tI/Odur\tBal\tST\tCT\tPID'\tNew AT\tNew BT\tTAT\tWT\tRT\tTQ")

for i in range(n):
    print(pid[i], "\t", at[i], "\t", bt[i], "\t", io_at[i],
          "\t", io_dur[i], "\t", bal[i], "\t", st[i], "\t",
          ct[i], "\t", pid[i] + "'", "\t", new_at[i], "\t",
          new_bt[i], "\t", tat[i], "\t", wt[i], "\t", rt[i],
          "\t", tq)

sum_bt = sum(bt)
sum_ct = sum(ct)
sum_tat = sum(tat)
sum_wt = sum(wt)
sum_rt = sum(rt)

avg_bt = round(sum_bt / n, 2)
avg_ct = round(sum_ct / n, 2)
avg_tat = round(sum_tat / n, 2)
avg_wt = round(sum_wt / n, 2)
avg_rt = round(sum_rt / n, 2)

print("\nSum")
print("BT =", sum_bt)
print("CT =", sum_ct)
print("TAT =", sum_tat)
print("WT =", sum_wt)
print("RT =", sum_rt)

print("\nAverage")
print("BT =", avg_bt)
print("CT =", avg_ct)
print("TAT =", avg_tat)
print("WT =", avg_wt)
print("RT =", avg_rt)

print("\nAverage CT  =", avg_ct)
print("Average TAT =", avg_tat)
print("Average WT  =", avg_wt)
print("Average RT  =", avg_rt)