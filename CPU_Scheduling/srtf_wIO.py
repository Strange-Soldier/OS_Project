# SRTF Scheduling with I/O

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


# Remaining CPU time
remaining1 = cpu1.copy()
remaining2 = cpu2.copy()

# 0 = waiting for first CPU
# 1 = doing I/O
# 2 = waiting for second CPU
# 3 = completed

state = [0] * n

io_end = [0] * n

completion = [0] * n
first_response = [-1] * n

time = 0
completed = 0

while completed < n:

    # Move processes from I/O back to ready queue
    for i in range(n):
        if state[i] == 1 and time >= io_end[i]:
            state[i] = 2

    shortest = -1

    # Find process with shortest remaining CPU burst
    for i in range(n):

        if arrival[i] <= time and state[i] != 3:

            if state[i] == 0 and remaining1[i] > 0:
                if shortest == -1 or remaining1[i] < remaining1[shortest]:
                    shortest = i

            elif state[i] == 2 and remaining2[i] > 0:
                if shortest == -1 or remaining2[i] < remaining2[shortest]:
                    shortest = i

    if shortest == -1:
        time += 1
        continue

    # Record response time
    if first_response[shortest] == -1:
        first_response[shortest] = time - arrival[shortest]

    # Execute process
    if state[shortest] == 0:

        remaining1[shortest] -= 1
        time += 1

        # First CPU burst finished
        if remaining1[shortest] == 0:

            if io[shortest] > 0:
                state[shortest] = 1
                io_end[shortest] = time + io[shortest]

            else:
                state[shortest] = 2

    elif state[shortest] == 2:

        remaining2[shortest] -= 1
        time += 1

        # Second CPU burst finished
        if remaining2[shortest] == 0:
            completion[shortest] = time
            state[shortest] = 3
            completed += 1


print("\nProcess\tAT\tCPU1\tIO\tCPU2\tCT\tRT\tTAT\tWT")

total_tat = 0
total_wt = 0
total_rt = 0

for i in range(n):

    total_cpu = cpu1[i] + cpu2[i]

    turnaround = completion[i] - arrival[i]

    # Waiting time = TAT - CPU time - I/O time
    waiting = turnaround - total_cpu - io[i]

    print(process[i], "\t", arrival[i], "\t", cpu1[i],
          "\t", io[i], "\t", cpu2[i], "\t", completion[i],
          "\t", first_response[i], "\t", turnaround, "\t", waiting)

    total_tat += turnaround
    total_wt += waiting
    total_rt += first_response[i]


print("\nAverage Turnaround Time =", total_tat / n)
print("Average Waiting Time =", total_wt / n)
print("Average Response Time =", total_rt / n)