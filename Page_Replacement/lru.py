# LRU Page Replacement

# simulate() runs the LRU algorithm and RETURNS the data (no printing).
# pages      = list of page numbers, e.g. [7, 0, 1, 2, ...]
# frame_size = how many frames memory has
def simulate(pages, frame_size):

    # Each physical frame is a FIXED slot. We track usage order separately so
    # the victim's slot is reused in place and the GUI frame table stays stable.
    slots = [None] * frame_size   # fixed memory slots (None = empty)
    recent = []                   # pages by recency (least recent first)
    hits = 0                      # page already in memory
    faults = 0                    # page had to be loaded
    snapshots = []                # one record per reference, for the GUI to replay

    # go through every page, keeping its position t
    for t in range(len(pages)):
        p = pages[t]

        if p in slots:
            # HIT: mark this page as most recently used (move to the back)
            hits = hits + 1
            recent.remove(p)
            recent.append(p)
            result = "H"
        else:
            # FAULT: page must be loaded
            faults = faults + 1
            if None in slots:
                # free frame available, use the first empty slot
                idx = slots.index(None)
                slots[idx] = p
                recent.append(p)
            else:
                # full: evict the LEAST recently used page, reuse ITS slot
                victim = recent.pop(0)
                idx = slots.index(victim)
                slots[idx] = p
                recent.append(p)
            result = "F"

        # snapshot the fixed slots exactly as they sit (None = empty frame)
        row = slots.copy()

        # save the state after handling this page
        snapshots.append({"t": t, "ref": p, "frames": row, "result": result})

    # hit ratio as a percentage (avoid dividing by zero)
    total = hits + faults
    if total > 0:
        hit_ratio = round(hits / total * 100, 2)
    else:
        hit_ratio = 0.0

    return {"snapshots": snapshots, "hits": hits,
            "faults": faults, "hit_ratio": hit_ratio}


# Old interactive program kept for direct runs; skipped when imported.
if __name__ == "__main__":

    pages = list(map(int, input("Enter the page reference string (space separated): ").split()))
    frame_size = int(input("Enter the number of frames: "))

    data = simulate(pages, frame_size)

    for snap in data["snapshots"]:
        real = [x for x in snap["frames"] if x is not None]
        word = "HIT  " if snap["result"] == "H" else "FAULT"
        print("Page", snap["ref"], "->", word, "Frames:", real)

    print()
    print("Total Hits:", data["hits"])
    print("Total Faults:", data["faults"])
