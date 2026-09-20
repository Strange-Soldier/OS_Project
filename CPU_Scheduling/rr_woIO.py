# Round Robin Scheduling without I/O

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

quantum = int(input("\nEnter Time Quantum: "))

remaining = burst.copy()

completion = [0] * n
waiting = [0] * n
turnaround = [0] * n
response = [-1] * n

queue = []

time = 0
completed = 0

# Add processes that arrive at time 0
for i in range(n):
    if arrival[i] == 0:
        queue.append(i)


while completed < n:

    # If queue is empty, move time to next process
    if len(queue) == 0:

        next_process = -1

        for i in range(n):
            if remaining[i] > 0:
                if next_process == -1 or arrival[i] < arrival[next_process]:
                    next_process = i

        time = arrival[next_process]
        queue.append(next_process)

    current = queue.pop(0)

    # Response time
    if response[current] == -1:
        response[current] = time - arrival[current]

    # Run process for time quantum or remaining time
    run_time = min(quantum, remaining[current])

    start_time = time
    time += run_time

    remaining[current] -= run_time

    # Add newly arrived processes to queue
    for i in range(n):
        if i != current and remaining[i] > 0:
            if arrival[i] > start_time and arrival[i] <= time:
                if i not in queue:
                    queue.append(i)

    # If process is completed
    if remaining[current] == 0:

        completion[current] = time
        turnaround[current] = completion[current] - arrival[current]
        waiting[current] = turnaround[current] - burst[current]

        completed += 1

    else:
        # Put current process at the end of queue
        queue.append(current)


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