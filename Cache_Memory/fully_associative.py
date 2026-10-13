# Fully Associative Cache
# A block can go in ANY line. When the cache is full we remove the oldest
# block (FIFO replacement).


def simulate(blocks, num_lines):
    # blocks    = list of memory block numbers, e.g. [7, 0, 1, 2, 0]
    # num_lines = how many lines the cache has

    cache = []          # blocks in the cache, oldest first
    hits = 0
    misses = 0
    snapshots = []

    for t in range(len(blocks)):
        b = blocks[t]

        if b in cache:
            # found it anywhere in the cache -> HIT
            hits = hits + 1
            line = cache.index(b)
            result = "H"
        else:
            # not there -> MISS
            misses = misses + 1
            if len(cache) < num_lines:
                cache.append(b)          # free line available
            else:
                cache.pop(0)             # remove the oldest block
                cache.append(b)
            line = cache.index(b)
            result = "M"

        # pad to a fixed length so the GUI can show every line
        row = cache.copy()
        while len(row) < num_lines:
            row.append(None)

        snapshots.append({"t": t, "block": b, "line": line,
                          "cache": row, "result": result})

    return build_result(snapshots, hits, misses)


# build_result() makes the summary numbers. Same in all three cache files.
def build_result(snapshots, hits, misses):
    total = hits + misses
    if total > 0:
        hit_ratio = round(hits / total * 100, 2)
        miss_ratio = round(misses / total * 100, 2)
    else:
        hit_ratio = 0.0
        miss_ratio = 0.0

    return {"snapshots": snapshots, "hits": hits, "misses": misses,
            "hit_ratio": hit_ratio, "miss_ratio": miss_ratio}


if __name__ == "__main__":
    blocks = list(map(int, input("Enter block reference string: ").split()))
    num_lines = int(input("Enter number of cache lines: "))

    data = simulate(blocks, num_lines)
    for s in data["snapshots"]:
        word = "HIT " if s["result"] == "H" else "MISS"
        print("Block", s["block"], word, s["cache"])
    print("\nHits:", data["hits"], " Misses:", data["misses"])
    print("Hit ratio:", data["hit_ratio"], "%  Miss ratio:", data["miss_ratio"], "%")
