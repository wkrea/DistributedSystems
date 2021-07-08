"""
    Preprocess the citizens file with lines of the format:
        <town_name> 123.000
    into
        <town_name>;123.000
"""

def read_file(filename):
    retval = []

    with open(filename) as in_file:
        for line in in_file:
            town_name, town_pop = line.rsplit(' ', 1)
            town_pop = town_pop.replace('.', '').replace('\n', '')
            retval.append((town_name, town_pop))

    return retval

def write_file(filename, data):
    with open(filename, 'w') as out_file:
        for pair in data:
            out_file.write("{};{}\n".format(pair[0], pair[1]))

if __name__ == "__main__":
    data = read_file("./citizens2.txt")
    print(data)
    write_file("./town_pop_map.csv", data)
