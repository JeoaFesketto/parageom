def _getlines(file, separator=' '):
    with open(file, "r") as f:
        data = [
            line.rstrip("\n").split(separator)
            if separator is not None
            else line.rstrip("\n")
            for line in f.readlines()
        ]
    for i in range(len(data)):
        data[i] = list(filter(None, data[i]))
    return data
