# SRTF Scheduling without I/O

n = int(input("Enter number of processes: "))

process = []
arrival = []
burst = []

for i in range(n):
    print("\nProcess", i + 1)
    at = int(input("Enter Arrival Time: "))
    bt = int(input("Enter Burst Time: "))

    process.append(i + 1)
    arrival.append(at)
    burst.append(bt)

remaining = burst.copy()

completion = [0] * n
turnaround = [0] * n
waiting = [0] * n
response = [-1] * n

time = 0
completed = 0

while completed < n:

    shortest = -1

    for i in range(n):
        if arrival[i] <= time and remaining[i] > 0:

            if shortest == -1 or remaining[i] < remaining[shortest]:
                shortest = i

    if shortest == -1:
        time += 1
        continue

    # First time the process gets CPU
    if response[shortest] == -1:
        response[shortest] = time - arrival[shortest]

    remaining[shortest] -= 1
    time += 1

    if remaining[shortest] == 0:
        completion[shortest] = time
        turnaround[shortest] = completion[shortest] - arrival[shortest]
        waiting[shortest] = turnaround[shortest] - burst[shortest]
        completed += 1


print("\nProcess\tAT\tBT\tCT\tTAT\tWT\tRT")

total_tat = 0
total_wt = 0
total_rt = 0

for i in range(n):
    print(process[i], "\t", arrival[i], "\t", burst[i],
          "\t", completion[i], "\t", turnaround[i],
          "\t", waiting[i], "\t", response[i])

    total_tat += turnaround[i]
    total_wt += waiting[i]
    total_rt += response[i]

print("\nAverage Turnaround Time =", total_tat / n)
print("Average Waiting Time =", total_wt / n)
print("Average Response Time =", total_rt / n)