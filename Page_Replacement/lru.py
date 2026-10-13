# LRU Page Replacement

# simulate() runs the LRU algorithm and RETURNS the data (no printing).
# pages      = list of page numbers, e.g. [7, 0, 1, 2, ...]
# frame_size = how many frames memory has
def simulate(pages, frame_size):

    frames = []        # pages in memory (least recently used at the front)
    hits = 0           # page already in memory
    faults = 0         # page had to be loaded
    snapshots = []     # one record per reference, for the GUI to replay

    # go through every page, keeping its position t
    for t in range(len(pages)):
        p = pages[t]

        if p in frames:
            # HIT: move this page to the back (it is now most recently used)
            hits = hits + 1
            frames.remove(p)
            frames.append(p)
            result = "H"
        else:
            # FAULT: page must be loaded
            faults = faults + 1
            if len(frames) < frame_size:
                # free frame available, just add it
                frames.append(p)
            else:
                # full: remove the LEAST recently used (front), add new one
                frames.pop(0)
                frames.append(p)
            result = "F"

        # fixed-length copy of frames (empty slots become None)
        row = frames.copy()
        while len(row) < frame_size:
            row.append(None)

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
