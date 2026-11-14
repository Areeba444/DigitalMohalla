"""Synthetic search catalogue and query set for the search evaluation (DA-25; plan item M9).

    python -I data/generators/search_catalogue.py      # writes data/derived/search/

Everything here is SYNTHETIC and written by the team from a template list (not copied from any
listing site). Standard library only, fixed seed: the same run gives byte-identical files, and
MANIFEST.json records their SHA-256 so the catalogue and queries can be frozen before anything is
measured (DA-25 section 6).

- catalogue.csv: about 150 items in the evaluator's community, several per need, a third with a
  common Roman Urdu name (to be checked by the team, open point S-E2), lenders with and without
  history; plus 20 decoys (other community, DRAFT, a blocking lender) that must never be returned.
- queries.csv: 26 test queries in the six types of DA-25 section 3, each with the need it stands
  for, so labellers judge the need and not the words; practice_queries.csv: 5 calibration queries.
- No address, coordinate or person field exists in any file.

Author: Minahil Kashif (Student 3, Module 10). Minahil writes the catalogue, queries and labels
but does not set ranking weights (plan rule: the scorer is not an author of retrieval or ranking).
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

SEED = 20261115
OUT = Path(__file__).resolve().parents[1] / "derived" / "search"

# need, category, title, Roman Urdu name or "", description, value band, deposit (PKR, record-only)
TEMPLATES: list[tuple[str, str, str, str, str, str, int]] = [
    ("holes_in_walls", "tools", "Hammer drill", "drill machine", "Corded hammer drill for brick and concrete walls, with masonry bits.", "MEDIUM", 1500),
    ("holes_in_walls", "tools", "Cordless drill driver", "", "Battery drill and screwdriver for wood and light walls; two batteries.", "MEDIUM", 1200),
    ("holes_in_walls", "tools", "Masonry drill bit set", "", "Set of bits from 4 to 12 mm for drilling into brick.", "LOW", 0),
    ("reach_high", "tools", "Aluminium step ladder", "seerhi", "Folding step ladder, six steps, light enough to carry upstairs.", "MEDIUM", 1000),
    ("reach_high", "tools", "Extension ladder", "lambi seerhi", "Two-part ladder that reaches a first-floor window or a water tank.", "HIGH", 3000),
    ("reach_high", "furniture", "Sturdy step stool", "", "Two-step stool for shelves and fans; holds an adult.", "LOW", 0),
    ("ironing", "appliances", "Steam iron", "istri", "Steam iron with a non-stick plate, for shirts and suits.", "LOW", 300),
    ("ironing", "furniture", "Ironing board", "istri stand", "Foldable ironing board with a heat-proof rest.", "LOW", 0),
    ("big_cooking", "appliances", "Large cooking pot for 40 people", "degh", "Heavy aluminium pot for dawat cooking, biryani or haleem.", "MEDIUM", 1000),
    ("big_cooking", "appliances", "Medium cooking pot", "degchi", "Steel pot with lid for family meals of ten.", "LOW", 300),
    ("big_cooking", "appliances", "Gas stove burner for outdoor cooking", "chulha", "Single high-flame burner for big pots, needs a gas cylinder.", "MEDIUM", 1500),
    ("serving", "appliances", "Serving dishes set", "", "Twelve steel serving dishes with lids for a dinner.", "LOW", 500),
    ("serving", "furniture", "Folding table", "", "Folding table that seats six, for guests or a stall.", "MEDIUM", 1000),
    ("serving", "furniture", "Plastic chairs, set of ten", "kursiyan", "Ten stackable chairs for guests on a roof or lawn.", "MEDIUM", 1000),
    ("sleeping_guests", "furniture", "Folding cot", "charpai", "Light folding bed for a guest, with a thin mattress.", "MEDIUM", 1000),
    ("sleeping_guests", "furniture", "Floor mattress", "gadda", "Single foam mattress, rolls up for storage.", "LOW", 300),
    ("sleeping_guests", "furniture", "Warm quilt", "razai", "Heavy winter quilt with a clean cover.", "LOW", 300),
    ("cleaning", "appliances", "Vacuum cleaner", "", "Bagless vacuum with a hose for sofas and curtains.", "MEDIUM", 1500),
    ("cleaning", "tools", "Pressure washer", "", "Electric pressure washer for cars, gates and the porch.", "HIGH", 3000),
    ("cleaning", "tools", "Long broom and dustpan", "jharu", "Soft broom with a long handle and a dustpan.", "LOW", 0),
    ("cleaning", "tools", "Bucket and mop", "balti pocha", "Bucket with a wringer and a cotton mop.", "LOW", 0),
    ("watering", "outdoor", "Garden hose, 20 m", "pani ka pipe", "Hose with a spray nozzle for plants and washing a car.", "LOW", 300),
    ("watering", "outdoor", "Watering can", "", "Ten-litre watering can for pots on a roof.", "LOW", 0),
    ("gardening", "outdoor", "Hand trowel and fork", "khurpa", "Small digging tools for pots and flower beds.", "LOW", 0),
    ("gardening", "outdoor", "Spade", "belcha", "Full-size spade for digging and moving soil.", "LOW", 300),
    ("gardening", "outdoor", "Hedge shears", "", "Long blades for trimming hedges and bushes.", "LOW", 300),
    ("gardening", "outdoor", "Electric lawn mower", "", "Corded mower for a small lawn.", "HIGH", 3000),
    ("cutting_wood", "tools", "Hand saw", "aari", "Saw for wood planks and branches.", "LOW", 300),
    ("cutting_wood", "tools", "Electric jigsaw", "", "Jigsaw for curved cuts in wood and plywood.", "MEDIUM", 1500),
    ("fixing", "tools", "Claw hammer", "hathora", "Steel hammer for nails and small repairs.", "LOW", 0),
    ("fixing", "tools", "Screwdriver set", "pechkas", "Twelve screwdrivers, flat and cross head.", "LOW", 0),
    ("fixing", "tools", "Pliers and wire cutter", "plas", "Pliers set for wiring and small fixes.", "LOW", 0),
    ("fixing", "tools", "Spanner set", "pana", "Open and ring spanners from 8 to 22 mm.", "LOW", 300),
    ("fixing", "tools", "Measuring tape and spirit level", "", "Five-metre tape and a level for hanging shelves straight.", "LOW", 0),
    ("power", "electronics", "Extension cord, 10 m", "", "Four sockets with a switch, for outdoor events.", "LOW", 0),
    ("power", "electronics", "UPS battery backup", "", "Keeps a fan and lights on during load shedding for two hours.", "HIGH", 5000),
    ("power", "electronics", "Rechargeable emergency light", "", "LED light that lasts six hours during power cuts.", "LOW", 300),
    ("cooling", "appliances", "Pedestal fan", "pankha", "Standing fan with three speeds.", "LOW", 500),
    ("cooling", "appliances", "Air cooler", "room cooler", "Water air cooler for one room.", "MEDIUM", 2000),
    ("baking", "appliances", "Electric oven", "", "Small oven for cakes and pizza.", "MEDIUM", 2000),
    ("baking", "appliances", "Hand mixer", "", "Two-speed mixer for cake batter and cream.", "LOW", 500),
    ("baking", "appliances", "Cake tins and rolling pin", "belan", "Round and square tins with a wooden rolling pin.", "LOW", 0),
    ("kitchen_small", "appliances", "Blender", "", "Blender with a grinder jar for chutney and shakes.", "LOW", 500),
    ("kitchen_small", "appliances", "Pressure cooker", "", "Five-litre pressure cooker for daal and meat.", "LOW", 500),
    ("kitchen_small", "appliances", "Flat griddle", "tawa", "Heavy iron griddle for roti and paratha.", "LOW", 0),
    ("kitchen_small", "appliances", "Rice cooker", "", "Electric rice cooker for eight people.", "LOW", 500),
    ("kids", "sports", "Children's bicycle", "cycle", "Bicycle for ages six to nine, with training wheels.", "MEDIUM", 1000),
    ("kids", "furniture", "Baby cot", "jhoola", "Wooden cot with sides for a baby.", "MEDIUM", 1500),
    ("kids", "media", "Picture books set", "", "Ten picture books in English and Urdu for young children.", "LOW", 0),
    ("sports", "sports", "Cricket bat and ball", "", "Full-size bat, tape ball and stumps for street cricket.", "LOW", 300),
    ("sports", "sports", "Badminton set", "", "Two rackets, shuttlecocks and a net.", "LOW", 300),
    ("sports", "sports", "Football", "", "Size five football, inflated.", "LOW", 0),
    ("travel", "outdoor", "Large suitcase", "attachi", "Hard suitcase with wheels for a long trip.", "MEDIUM", 1000),
    ("travel", "outdoor", "Camping tent for four", "", "Tent with poles and pegs for a family trip.", "MEDIUM", 1500),
    ("travel", "outdoor", "Cool box", "", "Insulated box that keeps drinks cold for a day.", "LOW", 300),
    ("rain", "outdoor", "Large umbrella", "chhatri", "Wide umbrella for two people.", "LOW", 0),
    ("study", "media", "O-level physics books", "", "Textbook and past papers for O-level physics.", "LOW", 0),
    ("study", "electronics", "Scientific calculator", "", "Calculator allowed in board exams.", "LOW", 300),
    ("event_sound", "electronics", "Bluetooth speaker", "", "Loud portable speaker for a small gathering.", "MEDIUM", 1500),
    ("event_sound", "electronics", "Projector", "", "Projector with an HDMI cable for a movie night.", "HIGH", 5000),
]
CONDITION_TEXT = {
    "NEW": "Barely used.",
    "GOOD": "Works well, light signs of use.",
    "FAIR": "Works, but shows its age.",
    "WORN": "Old but still usable.",
}
VARIANTS = [("", "GOOD"), ("Older ", "FAIR"), ("Nearly new ", "NEW")]
LENDERS = [f"L{i:02d}" for i in range(1, 21)]  # L01 to L08 have loan history; L09 to L20 are new
EST = set(LENDERS[:8])

QUERIES = [  # id, type, query text, the need it stands for (what labellers judge)
    ("Q01", "exact", "hammer drill", "a hammer drill"),
    ("Q02", "exact", "steam iron", "an iron for clothes"),
    ("Q03", "exact", "pressure cooker", "a pressure cooker"),
    ("Q04", "exact", "folding table", "a table that folds for guests"),
    ("Q05", "exact", "extension ladder", "a tall ladder"),
    ("Q06", "need", "something to make holes in a brick wall", "drilling into masonry"),
    ("Q07", "need", "keep the lights on during load shedding", "backup power or light in a power cut"),
    ("Q08", "need", "cook for a big family dinner", "large pots or burners for many guests"),
    ("Q09", "need", "guests are staying the night", "somewhere for a guest to sleep"),
    ("Q10", "need", "trim the bushes in my garden", "hedge or plant cutting tools"),
    ("Q11", "need", "clean the car and the porch", "washing outdoor surfaces"),
    ("Q12", "need", "reach the ceiling fan to clean it", "something to stand on to reach high"),
    ("Q13", "need", "it is very hot in my room", "cooling a room"),
    ("Q14", "roman_urdu", "seerhi chahiye", "a ladder"),
    ("Q15", "roman_urdu", "istri", "an iron for clothes"),
    ("Q16", "roman_urdu", "degh for dawat", "a very large cooking pot"),
    ("Q17", "roman_urdu", "charpai ya gadda", "a bed or mattress for a guest"),
    ("Q18", "roman_urdu", "pani ka pipe", "a garden hose"),
    ("Q19", "misspelling", "lader", "a ladder"),
    ("Q20", "misspelling", "screw driver", "screwdrivers"),
    ("Q21", "misspelling", "vaccum", "a vacuum cleaner"),
    ("Q22", "category", "garden tools", "any tool for gardening"),
    ("Q23", "category", "kitchen appliances for baking", "anything for baking"),
    ("Q24", "category", "sports equipment for kids", "sports or play items for children"),
    ("Q25", "no_answer", "car jack", "lifting a car to change a tyre (nothing in the catalogue)"),
    ("Q26", "no_answer", "wedding dress", "formal clothing (nothing in the catalogue)"),
]
PRACTICE = [
    ("P1", "exact", "blender", "a blender"),
    ("P2", "need", "fix a loose cupboard door", "small hand tools for repairs"),
    ("P3", "roman_urdu", "tawa", "a griddle for roti"),
    ("P4", "misspelling", "umbrela", "an umbrella"),
    ("P5", "category", "travel gear", "anything for a trip"),
]


def catalogue(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    n = 0
    for t, (need, cat, title, roman, desc, band, deposit) in enumerate(TEMPLATES):
        # 30 templates with three variants and 30 with two: 150 items, every need covered
        for prefix, cond in VARIANTS[: 3 if t < 30 else 2]:
            n += 1
            # a third of items carry the Roman Urdu name in search_terms (DA-25 section 2)
            terms = roman if roman and n % 3 != 2 else ""
            lender = rng.choice(LENDERS)
            rows.append(
                {
                    "item_key": f"C{n:03d}",
                    "need": need,
                    "category": cat,
                    "title": f"{prefix}{title[0].lower() + title[1:] if prefix else title}",
                    "description": f"{desc} {CONDITION_TEXT[cond]}",
                    "search_terms": terms,
                    "condition": cond,
                    "value_band": band,
                    "deposit_amount": deposit,
                    "lender": lender,
                    "lender_has_history": lender in EST,
                    "decoy": "NONE",
                    "synthetic": True,
                }
            )
    assert len(rows) == 150, len(rows)
    for i, kind in enumerate(["OTHER_COMMUNITY"] * 8 + ["DRAFT"] * 6 + ["BLOCKING_LENDER"] * 6):
        base = TEMPLATES[(i * 7) % len(TEMPLATES)]
        rows.append(
            {
                "item_key": f"D{i + 1:02d}",
                "need": base[0],
                "category": base[1],
                "title": base[2],
                "description": f"{base[4]} {CONDITION_TEXT['GOOD']}",
                "search_terms": base[3],
                "condition": "GOOD",
                "value_band": base[5],
                "deposit_amount": base[6],
                "lender": "LBLOCK" if kind == "BLOCKING_LENDER" else rng.choice(LENDERS),
                "lender_has_history": False,
                "decoy": kind,
                "synthetic": True,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    items = catalogue(rng)
    write_csv(OUT / "catalogue.csv", items)
    for name, qs in (("queries.csv", QUERIES), ("practice_queries.csv", PRACTICE)):
        write_csv(OUT / name, [{"query_id": q, "type": t, "text": x, "need": nd} for q, t, x, nd in qs])
    files = ["catalogue.csv", "queries.csv", "practice_queries.csv"]
    manifest = {
        "synthetic": True,
        "seed": SEED,
        "items": sum(1 for r in items if r["decoy"] == "NONE"),
        "decoys": sum(1 for r in items if r["decoy"] != "NONE"),
        "with_roman_urdu_name": sum(1 for r in items if r["search_terms"] and r["decoy"] == "NONE"),
        "queries": len(QUERIES),
        "practice_queries": len(PRACTICE),
        "sha256": {f: hashlib.sha256((OUT / f).read_bytes()).hexdigest() for f in files},
        "frozen": False,  # set to true by the team when DA-25 step 1 is signed off
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"search catalogue: {manifest['items']} items, {manifest['decoys']} decoys, "
          f"{manifest['queries']} queries -> {OUT}")


if __name__ == "__main__":
    main()
