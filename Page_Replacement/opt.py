# Optimal Page Replacement

# simulate() runs the OPTIMAL algorithm and RETURNS the data (no printing).
# It needs the WHOLE pages list up front, because it looks into the future
# to decide which page to remove.
def simulate(pages, frame_size):

    frames = []        # pages currently in memory
    hits = 0           # page already in memory
    faults = 0         # page had to be loaded
    snapshots = []     # one record per reference, for the GUI to replay

    # go through every page by its position i
    for i in range(len(pages)):
        p = pages[i]

        if p in frames:
            # HIT: page already in memory
            hits = hits + 1
            result = "H"
        else:
            # FAULT: page must be loaded
            faults = faults + 1
            if len(frames) < frame_size:
                # free frame available, just add it
                frames.append(p)
            else:
                # full: remove the page that is used FARTHEST in the future
                future = pages[i + 1:]          # pages still to come
                farthest = -1
                page_to_remove = frames[0]

                for f in frames:
                    if f not in future:
                        # this page is never needed again -> best to remove
                        page_to_remove = f
                        break
                    else:
                        # remember the one used latest
                        pos = future.index(f)
                        if pos > farthest:
                            farthest = pos
                            page_to_remove = f

                frames.remove(page_to_remove)
                frames.append(p)
            result = "F"

        # fixed-length copy of frames (empty slots become None)
        row = frames.copy()
        while len(row) < frame_size:
            row.append(None)

        # save the state after handling this page
        snapshots.append({"t": i, "ref": p, "frames": row, "result": result})

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
