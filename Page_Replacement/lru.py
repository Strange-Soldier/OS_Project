# LRU Page Replacement

pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
frame_size = 3

frames = []
hits = 0
faults = 0

for p in pages:
    if p in frames:
        hits = hits + 1
        frames.remove(p)   
        frames.append(p)  
        print("Page", p, "-> HIT   Frames:", frames)
    else:
        faults = faults + 1
        if len(frames) < frame_size:
            frames.append(p)
        else:
            frames.pop(0)     
            frames.append(p)
        print("Page", p, "-> FAULT Frames:", frames)

print()
print("Total Hits:", hits)
print("Total Faults:", faults)