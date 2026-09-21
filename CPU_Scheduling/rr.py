n = int(input("Enter number of processes: "))

pid = []
at = []
bt = []

for i in range(n):
    print("\nEnter details for process", i + 1)
    pid.append(input("Enter PID: "))
    at.append(int(input("Enter Arrival Time: ")))
    bt.append(int(input("Enter Burst Time: ")))

tq = int(input("\nEnter Time Quantum (Enter 2 for default): "))

if tq <= 0:
    tq = 2

remaining = bt.copy()

st = [-1] * n
ct = [0] * n
tat = [0] * n
wt = [0] * n
rt = [0] * n

done = [0] * n

queue = []
time = 0
count = 0

print("\nExecution")

while count < n:

    for i in range(n):
        if at[i] <= time and done[i] == 0 and i not in queue:
            if remaining[i] > 0:
                queue.append(i)

    if len(queue) == 0:
        time = time + 1
        continue

    current = queue.pop(0)

    if st[current] == -1:
        st[current] = time
        rt[current] = st[current] - at[current]

    run = 0

    while run < tq and remaining[current] > 0:

        remaining[current] = remaining[current] - 1
        time = time + 1
        run = run + 1

        for i in range(n):
            if at[i] <= time and done[i] == 0 and i != current:
                if remaining[i] > 0 and i not in queue:
                    queue.append(i)

    print("\nTime =", time)
    print("Ready Queue:", end=" ")

    for i in queue:
        print(pid[i], end=" ")

    print()
    print("Running:", pid[current])
    print("Bal:", remaining[current])

    if remaining[current] == 0:

        ct[current] = time
        tat[current] = ct[current] - at[current]
        wt[current] = tat[current] - bt[current]

        done[current] = 1
        count = count + 1

    else:
        queue.append(current)

print("\n")
print("PID\tAT\tBT\tST\tCT\tTAT\tWT\tRT\tTQ")

for i in range(n):
    print(pid[i], "\t", at[i], "\t", bt[i], "\t", st[i],
          "\t", ct[i], "\t", tat[i], "\t", wt[i],
          "\t", rt[i], "\t", tq)

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