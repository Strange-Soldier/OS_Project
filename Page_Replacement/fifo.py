# FIFO Page Replacement

pages = list(map(int, input("Enter the page reference string (space separated): ").split()))
frame_size = int(input("Enter the number of frames: "))

frames = []
hits = 0
faults = 0

for p in pages:
    if p in frames:
        hits = hits + 1
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