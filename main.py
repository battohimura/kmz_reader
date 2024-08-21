import requests
import json
from lxml import etree
from zipfile import ZipFile

BLOCKS = {
    "001": {1: "Monday", 4: "Thursday"},
    "002": {2: "Tuesday", 5: "Friday"},
    "003": {3: "Wednesday", 6: "Saturday"},
    "004": {1: "Monday", 3: "Wednesday", 5: "Friday"},
    "005": {2: "Tuesday", 4: "Thursday", 6: "Saturday"},
    "011": {1: "Monday"},
    "012": {2: "Tuesday"},
    "013": {3: "Wednesday"},
    "014": {4: "Thursday"},
    "015": {5: "Friday"},
    "016": {6: "Saturday"},
    "021": {1: "Monday", 3: "Wednesday"},
    "022": {1: "Monday", 5: "Friday"},
    "023": {2: "Tuesday", 4: "Thursday"},
    "024": {2: "Tuesday", 6: "Saturday"},
    "025": {3: "Wednesday", 5: "Friday"},
    "026": {4: "Thursday", 6: "Saturday"},
}

def read_file():
    try:
        with ZipFile("BLOQUES AREQUIPA.kmz", 'r') as kmz:
            with kmz.open('doc.kml', 'r') as kml_file:
                kml_content = kml_file.read()
                return etree.fromstring(kml_content)
    except Exception as e:
        print(f"File with errors: {e}")

def find_element(namespace, element, children, is_list = False):
    if element is None:
        return [] if is_list else None
    return getattr(
        element,
        'findall' if is_list else 'find'
    )(f"{{{namespace}}}{children}")

def get_zone_name(name, description):
    description_splited = description.split("<br>")
    route_name = "_".join(description_splited[1].rstrip().split(" "))
    return f"{name}{route_name}"

def get_zone_days(zone_name):
    return BLOCKS.get(zone_name).values()

def is_valid_coordinate(coord):
    if not coord or coord == "0":
        return False
    return coord.replace('.', '').replace("-", "").isdigit()

def clean_coordinates(string_coordinates):
    cleaned_coordinates = []
    coordinates = string_coordinates.replace('0\n', '').replace(' ', '').strip().split(',')
    valid_coordinates = [
        float(coord) for coord in coordinates
        if is_valid_coordinate(coord)
    ]
    valid_coordinates_length = len(valid_coordinates)
    if valid_coordinates_length % 2 != 0:
        print(f'Not valid coordinate found {valid_coordinates}')
    cleaned_coordinates = [
        {'lng': coordinates[range_index], 'lat': coordinates[range_index + 1]}
        for range_index in range(0, len(valid_coordinates), 2)
    ]
    return cleaned_coordinates


def get_coordinates_and_names(root, namespace):
    coordinates_to_save = []
    document = find_element(namespace, root, "Document")
    if document is None:
        print(f"Document not found in file with namespace: {namespace}")
    folder = find_element(namespace, document, "Folder")
    if folder is None:
        print(f"Folder not found in file with namespace: {namespace}")

    placemarks = find_element(namespace, folder, "Placemark", True)
    for placemark in placemarks:
        name = find_element(namespace, placemark, "name")
        description = find_element(namespace, placemark, "description")
        zone_name = get_zone_name(name.text, description.text)
        zone_day = get_zone_days(name.text)
        polygon = find_element(namespace, placemark, "Polygon")
        outer_boundary = find_element(namespace, polygon, "outerBoundaryIs")
        linear_ring = find_element(namespace, outer_boundary, "LinearRing")
        coordinates = find_element(namespace, linear_ring, "coordinates")
        if coordinates is not None and coordinates.text:
            cleaned_coordinates = clean_coordinates(coordinates.text)
            coordinates_to_save.append((cleaned_coordinates, zone_name, zone_day))
    return coordinates_to_save

def make_request(coordinates):
    for coord, name, day in coordinates:
        data = {
            "name": name,
            "schedules": list(day),
            "coordinates": json.dumps(coord)
        }
        response = requests.post("http://localhost:8000/v1/zones/", json=data, headers={"Content-Type": "application/json", "Authorization": "Token 769762086526fbeb51bb4c6269906e6d705ab224"})
        print(response.json())
    print('Request finished')

if __name__ == "__main__":
    root = read_file()
    namespace = root.nsmap.get("kml")

    coordinates = get_coordinates_and_names(root, namespace)
    make_request(coordinates)