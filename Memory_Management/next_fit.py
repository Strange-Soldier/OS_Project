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

print("     NEXT FIT:-")


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

start = 0

for i in range(p):
    allocated = 0
    count = 0
    j = start

    while count < n:

        if holes[j] >= processes[i]:
            old_size = holes[j]
            holes[j] = holes[j] - processes[i]
            allocated = 1
            start = j

            process_name = "P" + str(i + 1)
            process_size = str(processes[i]) + " KB"
            hole_name = "H" + str(j + 1)
            hole_size = str(old_size) + " KB"
            remaining = str(holes[j]) + " KB"

            print("| " + process_name + " " * (8 - len(process_name)) +
                  "| " + process_size + " " * (13 - len(process_size)) +
                  "| " + hole_name + " " * (16 - len(hole_name)) +
                  "| " + hole_size + " " * (12 - len(hole_size)) +
                  "| " + remaining + " " * (16 - len(remaining)) + "|")

            break

        j = j + 1

        if j == n:
            j = 0

        count = count + 1

    if allocated == 0:
        process_name = "P" + str(i + 1)
        process_size = str(processes[i]) + " KB"

        print("| " + process_name + " " * (8 - len(process_name)) +
              "| " + process_size + " " * (13 - len(process_size)) +
              "| Not Allocated   | -           | -               |")

print("+---------+--------------+-----------------+-------------+-----------------+")