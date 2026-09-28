n = int(input("Enter number of processes: "))

pid = []
at = []
bt = []

for i in range(n):
    print("\nEnter details for process", i + 1)
    pid.append(input("Enter PID: "))
    at.append(int(input("Enter Arrival Time: ")))
    bt.append(int(input("Enter Burst Time: ")))

remaining = bt.copy()

st = [-1] * n
ct = [0] * n
tat = [0] * n
wt = [0] * n
rt = [0] * n

done = [0] * n

time = 0
count = 0

print("\nExecution")

while count < n:

    small = -1

    for i in range(n):

        if done[i] == 0 and at[i] <= time and remaining[i] > 0:

            if small == -1:
                small = i

            elif remaining[i] < remaining[small]:
                small = i

    if small == -1:
        time = time + 1
        continue

    if st[small] == -1:
        st[small] = time
        rt[small] = st[small] - at[small]

    remaining[small] = remaining[small] - 1
    time = time + 1

    print("\nTime =", time)
    print("Ready Queue:", end=" ")

    for i in range(n):
        if done[i] == 0 and at[i] <= time and remaining[i] > 0:
            if i != small:
                print(pid[i], end=" ")

    print()
    print("Running:", pid[small])
    print("Bal:", remaining[small])

    if remaining[small] == 0:

        ct[small] = time
        tat[small] = ct[small] - at[small]
        wt[small] = tat[small] - bt[small]

        done[small] = 1
        count = count + 1

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