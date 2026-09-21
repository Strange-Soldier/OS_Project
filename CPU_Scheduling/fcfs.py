n = int(input("Enter number of processes: "))

pid = []
at = []
bt = []

for i in range(n):
    print("\nEnter details for process", i + 1)
    pid.append(input("Enter PID: "))
    at.append(int(input("Enter Arrival Time: ")))
    bt.append(int(input("Enter Burst Time: ")))

for i in range(n):
    for j in range(i + 1, n):
        if at[i] > at[j]:
            at[i], at[j] = at[j], at[i]
            bt[i], bt[j] = bt[j], bt[i]
            pid[i], pid[j] = pid[j], pid[i]

st = [0] * n
ct = [0] * n
tat = [0] * n
wt = [0] * n
rt = [0] * n

time = 0

print("\nExecution")

for i in range(n):

    if time < at[i]:
        time = at[i]

    st[i] = time
    rt[i] = st[i] - at[i]

    print("\nTime =", time)
    print("Ready Queue:", pid[i:])
    print("Running:", pid[i])

    time = time + bt[i]

    ct[i] = time
    tat[i] = ct[i] - at[i]
    wt[i] = tat[i] - bt[i]

print("\n")
print("PID\tAT\tBT\tST\tCT\tTAT\tWT\tRT")

for i in range(n):
    print(pid[i], "\t", at[i], "\t", bt[i], "\t", st[i],
          "\t", ct[i], "\t", tat[i], "\t", wt[i], "\t", rt[i])

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