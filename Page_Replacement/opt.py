# Optimal Page Replacement

pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
frame_size = 3

frames = []
hits = 0
faults = 0

for i in range(len(pages)):
    p = pages[i]

    if p in frames:
        hits = hits + 1
        print("Page", p, "-> HIT   Frames:", frames)
    else:
        faults = faults + 1
        if len(frames) < frame_size:
            frames.append(p)
        else:
           
            future = pages[i+1:]
            farthest = -1
            page_to_remove = frames[0]

            for f in frames:
                if f not in future:
                    page_to_remove = f
                    break
                else:
                    pos = future.index(f)
                    if pos > farthest:
                        farthest = pos
                        page_to_remove = f

            frames.remove(page_to_remove)
            frames.append(p)

        print("Page", p, "-> FAULT Frames:", frames)

print()
print("Total Hits:", hits)
print("Total Faults:", faults)