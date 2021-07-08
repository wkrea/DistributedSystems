"""
    Script that converts a CSV file with lines of the format
        <zipcode>;<town_name>;<lat>;<long>;<google-maps link>
    into
        <town_name>;<lat>;<long>
"""

def read_file(zipcode_file):
    retval = []

    with open(zipcode_file) as in_file:
        for line in in_file:
            line_list = line.split(";")
            
            town_name = line_list[1]
            town_lat  = line_list[2]
            town_long = line_list[3]

            retval.append((town_name, town_lat, town_long))
    return retval

def write_file(filename, data):
    with open(filename, 'w') as out_file:
        for pair in data:
            out_file.write("{};{};{}\n".format(pair[0], pair[1], pair[2]))

if __name__ == "__main__":
    data = read_file("./zipcodes_utf8.csv")
    print(data)
    write_file("./coord_map.csv", data)