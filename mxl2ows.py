import sys
from itertools import chain
import xmltodict
import pyperclip

A_Z = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

steps = {
    "C": 1,
    "D": 2,
    "E": 3,
    "F": 4,
    "G": 5,
    "A": 6,
    "B": 7
}
types = {
    "whole": 16,
    "half": 8,
    "quarter": 4,
    "eighth": 2,
    "16th": 0,
    "32nd": 0
}


def get_note_detail(n):
    return {
        "tie": n.get("tie", {}).get("@type"),
        "staff": n.get("staff"),
        "dot": n.get("dot"),
        "type": n.get("type"),
        "step": n.get("pitch", {}).get("step"),
        "alter": n.get("pitch", {}).get("alter"),
        "octave": n.get("pitch", {}).get("octave"),
    } if n.get("pitch") is not None else None


def get_notes(m):
    if type(m["note"]) is list:
        return list(map(get_note_detail, m["note"]))
    else:
        return get_note_detail(m["note"])


def note_to_array(note):
    _ = [{
             "1": "A",
             "2": "B",
             None: "A"
         }[note["staff"]]]
    if note["tie"] is "stop":
        _.append(0)
    else:
        _.append(int(note["octave"]) * 100)
        if note["alter"] is None:
            _[-1] += steps[note["step"]]
        else:
            _[-1] += (steps[note["step"]] + (7 if note["alter"] is '1' else 6))
    if note["dot"] is None:
        _ += (types[note["type"]] - 1) * [0]
    else:
        _ += int((types[note["type"]] - 1) + (types[note["type"]] / 2)) * [0]
    return _


if __name__ == '__main__':

    with open(sys.argv[1], encoding="utf8") as f:
    # with open("blackkey.musicxml", encoding="utf8") as f:
        xml_content = f.read().replace("<dot/>", "<dot>1</dot>")

    d = xmltodict.parse(xml_content)
    notes = []
    measure = d.get("score-partwise", {}).get("part", {}).get("measure")

    if type(measure) is list:
        notes += list(filter(lambda x: x is not None, map(get_notes, measure)))
    else:
        notes += get_notes(measure)

    notes = list(filter(lambda x: x is not None, list(chain.from_iterable(notes))))
    array = list(map(note_to_array, notes))
    print(array)
    slot1_array = list(chain.from_iterable(filter(lambda x: x[0] == "A", array)))
    slot2_array = list(chain.from_iterable(filter(lambda x: x[0] == "B", array)))

    slot1_array = list(filter(lambda x: x != "A", slot1_array))
    slot2_array = list(filter(lambda x: x != "B", slot2_array))

    slot1_array = [slot1_array[i:i + 1000] for i in range(0, len(slot1_array), 1000)]
    slot2_array = [slot2_array[i:i + 1000] for i in range(0, len(slot2_array), 1000)]


    def array_to_script(s, a):
        action_example = r"""
        Set Player Variable(Players In Slot({slot}, Team 1), {var_name},{append}Empty Array,{values});
        """
        result_text = ""
        for i in range(len(a)):
            values = ""
            counter = 0
            for member in a[i]:
                values += str(member) + "),"
                counter += 1
            values = values[:-1]
            result_text += action_example.format(
                slot=s,
                var_name=A_Z[i],
                append=counter * "Append To Array(",
                values=values
            )

        return result_text


    text = array_to_script(0, slot1_array) + array_to_script(1, slot2_array)
    text = "actions{" + text + "}"
    print(text)
    pyperclip.copy(text)
