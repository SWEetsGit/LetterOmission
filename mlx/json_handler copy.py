import json
import os


# Load the json
def get_json(json_file):
    if not os.path.exists(json_file):
        return {}
    with open(json_file, "r", encoding="utf-8") as file:
        return json.load(file)


def append_to_json(json_file, new_data):
    data = get_json(json_file)

    data.update(new_data)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Append string to list
def append_to_json_obj(json_file, json_key, new_data):
    data = get_json(json_file)

    if json_key in data:
        data[json_key][-1] += new_data
    else:
        data[json_key] = [new_data]

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Add new element (string) to list
def append_new_element_to_json_obj(json_file, json_key):
    data = get_json(json_file)

    if json_key in data:
        data[json_key].append("")
    else:
        data[json_key] = [""]

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
