# FIFO Page Replacement

# simulate() runs the FIFO algorithm and RETURNS the data (no printing).
# pages      = list of page numbers, e.g. [7, 0, 1, 2, ...]
# frame_size = how many frames memory has
def simulate(pages, frame_size):

    # Each physical frame is a FIXED slot. slots[i] stays put until that
    # specific frame is chosen as the victim, so the GUI frame table does
    # not shuffle pages between rows on every eviction.
    slots = [None] * frame_size   # fixed memory slots (None = empty)
    order = []                    # pages in the order they entered (FIFO queue)
    hits = 0                      # how many times the page was already in memory
    faults = 0                    # how many times we had to load the page
    snapshots = []                # one record per reference, for the GUI to replay

    # go through every page in the reference string, keeping its position t
    for t in range(len(pages)):
        p = pages[t]

        if p in slots:
            # page already in memory -> HIT (nothing changes in frames)
            hits = hits + 1
            result = "H"
        else:
            # page not in memory -> FAULT (we must load it)
            faults = faults + 1
            if None in slots:
                # there is still an empty frame, use the first free slot
                idx = slots.index(None)
                slots[idx] = p
                order.append(p)
            else:
                # memory is full: evict the OLDEST page, reuse ITS slot
                victim = order.pop(0)
                idx = slots.index(victim)
                slots[idx] = p
                order.append(p)
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

    # hand everything back to the caller as one dictionary
    return {"snapshots": snapshots, "hits": hits,
            "faults": faults, "hit_ratio": hit_ratio}


# The old interactive program is kept here so running the file still works,
# but it NO LONGER runs when the file is imported by the GUI.
if __name__ == "__main__":

    pages = list(map(int, input("Enter the page reference string (space separated): ").split()))
    frame_size = int(input("Enter the number of frames: "))

    # use the function above, then print exactly like before
    data = simulate(pages, frame_size)

    for snap in data["snapshots"]:
        # show only the real frames (drop the None padding) like the old output
        real = [x for x in snap["frames"] if x is not None]
        word = "HIT  " if snap["result"] == "H" else "FAULT"
        print("Page", snap["ref"], "->", word, "Frames:", real)

    print()
    print("Total Hits:", data["hits"])
    print("Total Faults:", data["faults"])
