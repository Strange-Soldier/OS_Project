# Optimal Page Replacement

pages = list(map(int, input("Enter the page reference string (space separated): ").split()))
frame_size = int(input("Enter the number of frames: "))

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