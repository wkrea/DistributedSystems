"""
    This python scripts converts a JSON list into a file that contains one
    element of the list on each line:
        [{'x':'a'}, {'y':'b'}, {'z':'c'}]
    into a CSV file with each line containing the following values:
        <halte_id>;<halte_name>;<lat>;<long>;<town_name>
"""
import json

def open_json(filename:str):
    with open(filename) as json_file:
        return json.load(json_file)

def halte_to_csv_line(halte_data:dict) -> str:
    halte_id   = halte_data['haltenummer']
    halte_naam = halte_data['omschrijving']
    halte_lat  = halte_data['geoCoordinaat']['latitude']
    halte_long = halte_data['geoCoordinaat']['longitude']
    halte_town = halte_data.get('omschrijvingGemeente', '')

    return "{};{};{};{};{}".format(halte_id, halte_naam, halte_lat, halte_long, halte_town)

def process_json(json_data:dict, out_file:str, filter):
    with open(out_file, 'w') as out_file:
        for halte in json_data["haltes"]:

            if filter and not 'omschrijvingGemeente' in halte:
                continue # skip

            # remove unwanted values
            if 'gemeentenummer' in halte:
                halte.pop("gemeentenummer")
            if 'links' in halte:
                halte.pop("links")

            out_file.write(halte_to_csv_line(halte) + "\n")

if __name__ == "__main__":
    json_data = open_json("stops.json")

    process_json(json_data, "converted_stops.csv", False)
