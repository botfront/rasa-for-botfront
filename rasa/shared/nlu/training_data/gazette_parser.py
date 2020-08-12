from typing import Text, List, Dict


def add_item_to_gazette(
    title: Text, item: Text, existing_gazettes: List[Dict[Text, List[Text]]]
) -> None:
    matches = [l for l in existing_gazettes if l["value"] == title]
    if not matches:
        existing_gazettes.append({"value": title, "gazette": [item]})
    else:
        gazette_els = matches[0]["gazette"]
        gazette_els.append(item)
