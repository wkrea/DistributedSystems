
import json

def get_popmap_lhs(popmap_filename):
    """
        Retrieve list of town names that are mappable with the population map.
    """

    towns = []

    with open(popmap_filename) as map_file:
        for line in map_file:
            town_name = line.split(";")[0]

            if not town_name in towns:
                towns.append(town_name)

    return towns

def get_townnamemap_rhs(town_name_map_filename):
    """
        Retrieve list of town names that are mapped to with the town name map.
    """

    towns = []

    with open(town_name_map_filename) as map_file:
        for line in map_file:
            town_name = line.split(";")[1].strip()

            if not town_name in towns:
                towns.append(town_name)

    return towns



if __name__ == "__main__":
    towns_map_rhs = get_townnamemap_rhs("./townname_map.csv")
    popmap_lhs = get_popmap_lhs("./town_pop_map.csv")

    i = 0

    for town in towns_map_rhs:
        if not town in popmap_lhs:
            i += 1
            print("Cannot find {}".format(town))

    print(i,"towns are missing from population map")

