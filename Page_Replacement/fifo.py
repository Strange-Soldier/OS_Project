# FIFO Page Replacement

# simulate() runs the FIFO algorithm and RETURNS the data (no printing).
# pages      = list of page numbers, e.g. [7, 0, 1, 2, ...]
# frame_size = how many frames memory has
def simulate(pages, frame_size):

    frames = []        # pages currently in memory (oldest at the front)
    hits = 0           # how many times the page was already in memory
    faults = 0         # how many times we had to load the page
    snapshots = []     # one record per reference, for the GUI to replay

    # go through every page in the reference string, keeping its position t
    for t in range(len(pages)):
        p = pages[t]

        if p in frames:
            # page already in memory -> HIT (nothing changes in frames)
            hits = hits + 1
            result = "H"
        else:
            # page not in memory -> FAULT (we must load it)
            faults = faults + 1
            if len(frames) < frame_size:
                # there is still an empty frame, just add the page
                frames.append(p)
            else:
                # memory is full: remove the OLDEST page (front), add new one
                frames.pop(0)
                frames.append(p)
            result = "F"

        # make a fixed-length copy of frames (fill empty slots with None)
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
