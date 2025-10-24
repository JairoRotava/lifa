

def group_files(L, size, step):
    starts = range(0, len(L), step)
    stops = [x + size for x in starts]
    groups = [(L*2)[start:stop] for start, stop in zip(starts, stops)]
    return groups

