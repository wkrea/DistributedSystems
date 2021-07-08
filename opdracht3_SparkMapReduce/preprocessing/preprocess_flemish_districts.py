"""
    This python file will convert a text file with lines of the formeat
        x: y, z
    into an equivalent file where each such line is split up into
        y x
        z x
    if x is not equal to y and x is not equal to z the line will be converted as follows
        x x
        y x
        z x
"""

def read_file(districts_filename:str) -> dict:
    retval = []
    processed_subtowns = []
    with open(districts_filename) as districts_file:
        for line in districts_file:
            line_head, line_body = [x.strip() for x in line.split(':')]

            body_list = [x.strip() for x in line_body.split(',')]

            if not line_head in body_list:
                body_list.append(line_head)

            for subtown in body_list:
                if subtown in processed_subtowns:
                    print("ALERT: attemped double mapping for", subtown)
                else:
                    retval.append((subtown, line_head))
                    processed_subtowns.append(subtown)

    return retval

def write_file(filename, pairs):
    with open(filename, 'w') as out_file:
        for pair in pairs:
            out_file.write("{};{}\n".format(pair[0], pair[1]))


if __name__ == "__main__":
    mapping = read_file("./flemish_districs.txt")
    write_file("townname_map.csv", mapping)