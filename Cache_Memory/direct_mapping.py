# Direct Mapping Cache
# Every block has ONE fixed line it must go to:  line = block % number_of_lines


def simulate(blocks, num_lines):
    # blocks    = list of memory block numbers, e.g. [7, 0, 1, 2, 0]
    # num_lines = how many lines the cache has

    cache = [None] * num_lines      # what is stored in each line
    hits = 0
    misses = 0
    snapshots = []

    for t in range(len(blocks)):
        b = blocks[t]
        line = b % num_lines        # this block can only go here

        if cache[line] == b:
            # the block we want is already in its line -> HIT
            hits = hits + 1
            result = "H"
        else:
            # wrong block (or empty) -> MISS, overwrite that line
            misses = misses + 1
            cache[line] = b
            result = "M"

        snapshots.append({"t": t, "block": b, "line": line,
                          "cache": cache.copy(), "result": result})

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
        print("Block", s["block"], "-> line", s["line"], word, s["cache"])
    print("\nHits:", data["hits"], " Misses:", data["misses"])
    print("Hit ratio:", data["hit_ratio"], "%  Miss ratio:", data["miss_ratio"], "%")
