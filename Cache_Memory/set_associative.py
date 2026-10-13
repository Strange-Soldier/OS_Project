# Set Associative Cache
# The cache is split into small sets. A block must go in one set
# (set = block % number_of_sets) but can use any line inside that set.
# When a set is full we remove its oldest block (FIFO replacement).


def simulate(blocks, num_lines, ways):
    # blocks    = list of memory block numbers, e.g. [7, 0, 1, 2, 0]
    # num_lines = total cache lines
    # ways      = how many lines are in each set

    num_sets = num_lines // ways
    if num_sets < 1:
        num_sets = 1

    # each set is a small list of blocks, oldest first
    sets = []
    for i in range(num_sets):
        sets.append([])

    hits = 0
    misses = 0
    snapshots = []

    for t in range(len(blocks)):
        b = blocks[t]
        s = b % num_sets            # which set this block belongs to

        if b in sets[s]:
            # already in its set -> HIT
            hits = hits + 1
            result = "H"
        else:
            # not there -> MISS
            misses = misses + 1
            if len(sets[s]) < ways:
                sets[s].append(b)       # free line in this set
            else:
                sets[s].pop(0)          # remove oldest block in this set
                sets[s].append(b)
            result = "M"

        # copy every set, padded so the GUI can show all lines
        state = []
        for one in sets:
            row = one.copy()
            while len(row) < ways:
                row.append(None)
            state.append(row)

        snapshots.append({"t": t, "block": b, "set": s,
                          "cache": state, "result": result})

    return build_result(snapshots, hits, misses, num_sets, ways)


# build_result() makes the summary numbers. Same idea as the other cache files.
def build_result(snapshots, hits, misses, num_sets, ways):
    total = hits + misses
    if total > 0:
        hit_ratio = round(hits / total * 100, 2)
        miss_ratio = round(misses / total * 100, 2)
    else:
        hit_ratio = 0.0
        miss_ratio = 0.0

    return {"snapshots": snapshots, "hits": hits, "misses": misses,
            "hit_ratio": hit_ratio, "miss_ratio": miss_ratio,
            "num_sets": num_sets, "ways": ways}


if __name__ == "__main__":
    blocks = list(map(int, input("Enter block reference string: ").split()))
    num_lines = int(input("Enter number of cache lines: "))
    ways = int(input("Enter lines per set (ways): "))

    data = simulate(blocks, num_lines, ways)
    for s in data["snapshots"]:
        word = "HIT " if s["result"] == "H" else "MISS"
        print("Block", s["block"], "-> set", s["set"], word, s["cache"])
    print("\nHits:", data["hits"], " Misses:", data["misses"])
    print("Hit ratio:", data["hit_ratio"], "%  Miss ratio:", data["miss_ratio"], "%")
