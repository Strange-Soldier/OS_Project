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

time = 0
count = 0

print("\nExecution")

while count < n:

    small = -1

    for i in range(n):
        if done_first[i] == 0 and at[i] <= time:

            if small == -1:
                small = i

            elif io_at[i] < io_at[small]:
                small = i

    if small == -1:
        for i in range(n):
            if done_first[i] == 1 and done_second[i] == 0:
                if new_at[i] <= time:
                    if small == -1:
                        small = i
                    elif new_bt[i] < new_bt[small]:
                        small = i

    if small == -1:
        time = time + 1
        continue

    if done_first[small] == 0:

        st[small] = time
        rt[small] = st[small] - at[small]

        print("\nTime =", time)
        print("Ready Queue:", end=" ")

        for i in range(n):
            if done_first[i] == 0 and at[i] <= time and i != small:
                print(pid[i], end=" ")

        print()
        print("Running:", pid[small])

        time = time + io_at[small]

        print("Bal:", 0)

        first_ct[small] = time
        new_at[small] = first_ct[small] + io_dur[small]

        done_first[small] = 1

        print("I/O Queue:", pid[small])
        print("I/O Start:", first_ct[small])
        print("I/O End:", new_at[small])

    else:

        print("\nTime =", time)
        print("Ready Queue:", end=" ")

        for i in range(n):
            if done_first[i] == 1 and done_second[i] == 0:
                if new_at[i] <= time and i != small:
                    print(pid[i], end=" ")

        print()
        print("Running:", pid[small])
        print("Bal:", new_bt[small])

        time = time + new_bt[small]

        ct[small] = time
        tat[small] = ct[small] - at[small]
        wt[small] = tat[small] - bt[small]

        done_second[small] = 1
        count = count + 1

print("\n")
print("PID\tAT\tBT\tI/Oat\tI/Odur\tBal\tST\tCT\tPID'\tNew AT\tNew BT\tTAT\tWT\tRT")

for i in range(n):
    print(pid[i], "\t", at[i], "\t", bt[i], "\t", io_at[i],
          "\t", io_dur[i], "\t", bal[i], "\t", st[i], "\t",
          ct[i], "\t", pid[i] + "'", "\t", new_at[i], "\t",
          new_bt[i], "\t", tat[i], "\t", wt[i], "\t", rt[i])

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