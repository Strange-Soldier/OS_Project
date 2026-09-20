# SRTF Scheduling - handles both cases (with I/O and without I/O)

n = int(input("Enter number of processes: "))

has_io = input("Does this system have I/O bursts? (y/n): ").strip().lower() == "y"

process = []
arrival = []
cpu1 = []
io = []
cpu2 = []

for i in range(n):
    print("\nProcess", i + 1)

    at = int(input("Enter Arrival Time: "))

    if has_io:
        b1 = int(input("Enter First CPU Burst: "))
        ib = int(input("Enter I/O Burst: "))
        b2 = int(input("Enter Second CPU Burst: "))
    else:
        b1 = int(input("Enter Burst Time: "))
        ib = 0
        b2 = 0

    process.append(i + 1)
    arrival.append(at)
    cpu1.append(b1)
    io.append(ib)
    cpu2.append(b2)

remaining1 = cpu1.copy()
remaining2 = cpu2.copy()

# state: 0 = waiting for first CPU, 1 = doing I/O, 2 = waiting for second CPU, 3 = completed
state = [0] * n
io_end = [0] * n

completion = [0] * n
first_response = [-1] * n

time = 0
completed = 0

while completed < n:

    # move processes from I/O back to ready queue
    for i in range(n):
        if state[i] == 1 and time >= io_end[i]:

            if remaining2[i] > 0:
                state[i] = 2
            else:
                # nothing left after I/O - process is done
                completion[i] = time
                state[i] = 3
                completed += 1

    shortest = -1

    # find the process with the shortest remaining CPU burst
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

    if first_response[shortest] == -1:
        first_response[shortest] = time - arrival[shortest]

    if state[shortest] == 0:

        remaining1[shortest] -= 1
        time += 1

        # first CPU burst finished
        if remaining1[shortest] == 0:

            if io[shortest] > 0:
                state[shortest] = 1
                io_end[shortest] = time + io[shortest]

            elif cpu2[shortest] > 0:
                state[shortest] = 2

            else:
                # no I/O and no second burst - process is done right here
                completion[shortest] = time
                state[shortest] = 3
                completed += 1

    elif state[shortest] == 2:

        remaining2[shortest] -= 1
        time += 1

        # second CPU burst finished
        if remaining2[shortest] == 0:
            completion[shortest] = time
            state[shortest] = 3
            completed += 1


# ---- results ----

total_tat = 0
total_wt = 0
total_rt = 0

if has_io:

    print("\nProcess\tAT\tCPU1\tIO\tCPU2\tCT\tRT\tTAT\tWT")

    for i in range(n):

        total_cpu = cpu1[i] + cpu2[i]
        turnaround = completion[i] - arrival[i]
        waiting = turnaround - total_cpu - io[i]

        print(process[i], "\t", arrival[i], "\t", cpu1[i],
              "\t", io[i], "\t", cpu2[i], "\t", completion[i],
              "\t", first_response[i], "\t", turnaround, "\t", waiting)

        total_tat += turnaround
        total_wt += waiting
        total_rt += first_response[i]

else:

    print("\nProcess\tAT\tBT\tCT\tTAT\tWT\tRT")

    for i in range(n):

        turnaround = completion[i] - arrival[i]
        waiting = turnaround - cpu1[i]

        print(process[i], "\t", arrival[i], "\t", cpu1[i],
              "\t", completion[i], "\t", turnaround,
              "\t", waiting, "\t", first_response[i])

        total_tat += turnaround
        total_wt += waiting
        total_rt += first_response[i]

print("\nAverage Turnaround Time =", total_tat / n)
print("Average Waiting Time =", total_wt / n)
print("Average Response Time =", total_rt / n)