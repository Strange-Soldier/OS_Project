# Worst Fit Memory Allocation
# Put each process in the LARGEST block that is big enough.


def simulate(blocks, processes):
    # blocks    = list of block sizes, e.g. [100, 500, 200]
    # processes = list of dicts like {"pid":"P1", "size":212}

    free = blocks.copy()
    taken = [None] * len(blocks)
    snapshots = []

    for t in range(len(processes)):
        p = processes[t]
        chosen = -1

        # check every block, keep the biggest one that fits
        for i in range(len(free)):
            if free[i] >= p["size"]:
                if chosen == -1 or free[i] > free[chosen]:
                    chosen = i

        if chosen != -1:
            free[chosen] = free[chosen] - p["size"]
            taken[chosen] = p["pid"]
            result = "OK"
        else:
            result = "FAIL"

        snapshots.append({"t": t, "pid": p["pid"], "size": p["size"],
                          "block": chosen if chosen != -1 else None,
                          "free": free.copy(), "taken": taken.copy(),
                          "result": result})

    return build_result(blocks, snapshots)


# build_result() makes the summary numbers. Same in all four memory files.
def build_result(blocks, snapshots):
    allocated = 0
    failed = 0
    for s in snapshots:
        if s["result"] == "OK":
            allocated = allocated + 1
        else:
            failed = failed + 1

    if snapshots:
        free_left = sum(snapshots[-1]["free"])
    else:
        free_left = sum(blocks)

    return {"blocks": blocks, "snapshots": snapshots,
            "allocated": allocated, "failed": failed,
            "free_left": free_left, "total": sum(blocks)}


if __name__ == "__main__":
    blocks = list(map(int, input("Enter block sizes (space separated): ").split()))
    sizes = list(map(int, input("Enter process sizes (space separated): ").split()))
    procs = [{"pid": "P%d" % (i + 1), "size": s} for i, s in enumerate(sizes)]

    data = simulate(blocks, procs)
    for s in data["snapshots"]:
        where = "Block %d" % (s["block"] + 1) if s["block"] is not None else "Not Allocated"
        print(s["pid"], "(", s["size"], ") ->", where)
    print("\nAllocated:", data["allocated"], " Failed:", data["failed"])
    print("Free left:", data["free_left"], "of", data["total"])
