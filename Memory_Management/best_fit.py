n = int(input("Enter number of holes: "))

holes = []

for i in range(n):
    size = int(input("Enter size of hole " + str(i + 1) + ": "))
    holes.append(size)

p = int(input("Enter number of processes: "))

processes = []

for i in range(p):
    size = int(input("Enter size of process P" + str(i + 1) + ": "))
    processes.append(size)

print()

print("     BEST FIT:-")


print()
print("+---------+-------------+")
print("| Hole    | Size        |")
print("+---------+-------------+")

for i in range(n):
    print("| H" + str(i + 1) + "      | " + str(holes[i]) + " KB" + " " * (7 - len(str(holes[i]))) + "|")

print("+---------+-------------+")

print()
print("+---------+-------------+")
print("| Process | Size        |")
print("+---------+-------------+")

for i in range(p):
    print("| P" + str(i + 1) + "      | " + str(processes[i]) + " KB" + " " * (7 - len(str(processes[i]))) + "|")

print("+---------+-------------+")

print()
print("+---------+--------------+-----------------+-------------+-----------------+")
print("| Process | Process Size | Allocated Hole  | Hole Before | Remaining Hole  |")
print("+---------+--------------+-----------------+-------------+-----------------+")

for i in range(p):
    best = -1

    for j in range(n):
        if holes[j] >= processes[i]:
            if best == -1 or holes[j] < holes[best]:
                best = j

    if best != -1:
        old_size = holes[best]
        holes[best] = holes[best] - processes[i]

        process_name = "P" + str(i + 1)
        process_size = str(processes[i]) + " KB"
        hole_name = "H" + str(best + 1)
        hole_size = str(old_size) + " KB"
        remaining = str(holes[best]) + " KB"

        print("| " + process_name + " " * (8 - len(process_name)) +
              "| " + process_size + " " * (13 - len(process_size)) +
              "| " + hole_name + " " * (16 - len(hole_name)) +
              "| " + hole_size + " " * (12 - len(hole_size)) +
              "| " + remaining + " " * (16 - len(remaining)) + "|")

    else:
        process_name = "P" + str(i + 1)
        process_size = str(processes[i]) + " KB"

        print("| " + process_name + " " * (8 - len(process_name)) +
              "| " + process_size + " " * (13 - len(process_size)) +
              "| Not Allocated   | -           | -               |")

print("+---------+--------------+-----------------+-------------+-----------------+")