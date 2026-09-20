# Round Robin Scheduling with I/O

n = int(input("Enter number of processes: "))

process = []
arrival = []
cpu1 = []
io = []
cpu2 = []

for i in range(n):
    print("\nProcess", i + 1)

    at = int(input("Enter Arrival Time: "))
    b1 = int(input("Enter First CPU Burst: "))
    ib = int(input("Enter I/O Burst: "))
    b2 = int(input("Enter Second CPU Burst: "))

    process.append(i + 1)
    arrival.append(at)
    cpu1.append(b1)
    io.append(ib)
    cpu2.append(b2)

quantum = int(input("\nEnter Time Quantum: "))

remaining1 = cpu1.copy()
remaining2 = cpu2.copy()

state = [0] * n
io_end = [0] * n
completion = [0] * n
response = [-1] * n
queue = []
time = 0
completed = 0

for i in range(n):
    if arrival[i] == 0:
        queue.append(i)

while completed < n:

    for i in range(n):
        if state[i] == 1 and time >= io_end[i]:
            state[i] = 2
            queue.append(i)

    if len(queue) == 0:

        next_time = -1

        for i in range(n):

            if state[i] == 0 and remaining1[i] > 0:

                if next_time == -1 or arrival[i] < next_time:
                    next_time = arrival[i]

            elif state[i] == 1:

                if next_time == -1 or io_end[i] < next_time:
                    next_time = io_end[i]

        time = next_time

        for i in range(n):

            if state[i] == 0 and arrival[i] <= time:
                if i not in queue:
                    queue.append(i)

            elif state[i] == 1 and io_end[i] <= time:
                state[i] = 2
                if i not in queue:
                    queue.append(i)

    current = queue.pop(0)

    if response[current] == -1:
        response[current] = time - arrival[current]

    if state[current] == 0:

        run_time = min(quantum, remaining1[current])

        remaining1[current] -= run_time
        time += run_time

        # Check I/O completion
        for i in range(n):
            if state[i] == 1 and io_end[i] <= time:
                state[i] = 2
                queue.append(i)

        # First CPU burst completed
        if remaining1[current] == 0:

            if io[current] > 0:
                state[current] = 1
                io_end[current] = time + io[current]

            else:
                state[current] = 2
                queue.append(current)

        else:
            queue.append(current)


    elif state[current] == 2:

        run_time = min(quantum, remaining2[current])

        remaining2[current] -= run_time
        time += run_time

        for i in range(n):
            if state[i] == 1 and io_end[i] <= time:
                state[i] = 2
                queue.append(i)

        if remaining2[current] == 0:

            completion[current] = time
            state[current] = 3
            completed += 1

        else:
            queue.append(current)


print("\nProcess\tAT\tCPU1\tIO\tCPU2\tCT\tRT\tTAT\tWT")

total_tat = 0
total_wt = 0
total_rt = 0

for i in range(n):

    total_cpu = cpu1[i] + cpu2[i]

    turnaround = completion[i] - arrival[i]

    waiting = turnaround - total_cpu - io[i]

    print(process[i], "\t", arrival[i], "\t", cpu1[i],
          "\t", io[i], "\t", cpu2[i], "\t", completion[i],
          "\t", response[i], "\t", turnaround, "\t", waiting)

    total_tat += turnaround
    total_wt += waiting
    total_rt += response[i]


print("\nAverage Turnaround Time =", total_tat / n)
print("Average Waiting Time =", total_wt / n)
print("Average Response Time =", total_rt / n)