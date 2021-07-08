
import json


def get_stop_towns(stops_filename):
    """
        Retieve list of town names of the stops.
    """

    towns = []

    with open(stops_filename) as stops_file:
        for line in stops_file:
            town_name = line.split(";")[-1].strip()

            if not town_name in towns:
                towns.append(town_name)

    return towns

def get_townnamemap_lhs(town_name_map_filename):
    """
        Retrieve list of town names that are mappable with the town name map.
    """

    towns = []

    with open(town_name_map_filename) as map_file:
        for line in map_file:
            town_name = line.split(";")[0]

            if not town_name in towns:
                towns.append(town_name)

    return towns


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

def get_coordmap_lhs(coordmap_filename):
    """
        Retrieve list of town names that are mappable with the coordinate map.
    """

    towns = []

    with open(coordmap_filename) as map_file:
        for line in map_file:
            town_name = line.split(";")[0]

            if not town_name in towns:
                towns.append(town_name)

    return towns

if __name__ == "__main__":
    towns_haltes = get_stop_towns("./converted_stops.csv")
    towns_map_lhs = get_townnamemap_lhs("./townname_map.csv")
    popmap_lhs = get_popmap_lhs("./town_pop_map.csv")
    coordmap_lhs = get_coordmap_lhs("./coord_map.csv")

    missing_townmap = []
    for town in towns_haltes:
        if not town in towns_map_lhs:
            missing_townmap.append(town)

    missing_popmap = []
    for town in towns_haltes:
        if not town in popmap_lhs:
            missing_popmap.append(town)

    missing_coordmap = []
    for town in towns_haltes:
        if not town in coordmap_lhs:
            missing_coordmap.append(town)

    print("Total towns:",len(towns_haltes))
    print("Missing from town name map:",len(missing_townmap))
    print("Missing from town pop map:",len(missing_popmap))
    print("Missing from town coord map:",len(missing_coordmap))
    print("Total in town map:",len(missing_townmap))
    print("Total in pop map:",len(popmap_lhs))
    print("Total in coord map:",len(coordmap_lhs))
