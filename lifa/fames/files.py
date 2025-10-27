

r"""
    Groups files in list

    Parameters
    ----------
    L : (M,) array
       List of files.
    step: int
       Step for grouping.
    size : int
       Size for each group

    Returns
    -------
    groups : arrays
    """
def group_files(L, step, size):
    starts = range(0, len(L)-size+1, step)
    stops = [x + size for x in starts]
    groups = [(L)[start:stop] for start, stop in zip(starts, stops)]
    return groups


