"""Text banks for synthetic reviews, dispute descriptions and messages.

All text is invented for this project (English with some Roman Urdu, as residents would write).
It exists so that legitimate reviews are DIFFERENT from each other (the earlier community set
had 17 distinct review texts for 484 ratings) and so that attack reviews can be made deliberately
similar. No real person's words are used.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------- legitimate reviews

_POS_OPEN = [
    "Smooth transaction, no issues at all.",
    "Bohat acha experience raha.",
    "Very responsible neighbour.",
    "Alhamdulillah sab theek raha.",
    "Great to deal with.",
    "Everything went as agreed.",
    "Acha banda hai, koi masla nahi hua.",
    "Polite and easy to coordinate with.",
    "Pehli dafa se hi bharosa ho gaya.",
    "Reliable person, happy to help again.",
    "Honest and straightforward.",
    "Time par aaye aur time par wapis kiya.",
    "Ten out of ten, neighbours like this make the lane better.",
    "Sab kuch clear tha pehle se, koi confusion nahi.",
    "A calm and decent person to deal with.",
    "Baat cheet bohat achi thi.",
    "No stress at all, would trust again.",
    "Mashallah bohat ikhlaq wala insan hai.",
    "Quick to confirm and quick to respond.",
    "Easy handover, easy return.",
]
_POS_DETAIL = [
    "The {item} came back clean and working.",
    "{item} bilkul waisa hi tha jaisa bataya tha.",
    "Handed over the {item} right on time.",
    "They even cleaned the {item} before returning it.",
    "{item} was in better shape than I expected.",
    "Message ka jawab foran mil jata hai.",
    "Pickup took five minutes, no fuss.",
    "Returned the {item} a day early.",
    "Explained how to use the {item} properly.",
    "Dono taraf se koi shikayat nahi.",
    "Kept me updated about timing.",
    "The {item} was exactly as described in the listing.",
    "I used the {item} on Saturday and it worked without a problem.",
    "{item} ka istemal theek raha, shukriya.",
    "Brought back the {item} with the charger and all the extras.",
    "We met outside the gate, very convenient.",
    "They checked the {item} with me before taking it.",
    "Even offered to pay for the cleaning of the {item}.",
    "{item} mere kaam aa gaya, waqt par mil gaya.",
    "Return ke waqt ek bar phone kar ke bata diya.",
    "Left a small thank-you note with the {item}.",
    "The {item} smelled fresh and looked unused.",
    "Was patient while I found the {item} in the store room.",
    "Handover was at the agreed hour, not a minute late.",
]
_POS_CLOSE = [
    "Would lend again.",
    "Dobara dena pasand karunga.",
    "JazakAllah!",
    "Thanks!",
    "Recommended.",
    "Highly appreciated.",
    "Allah aap ko khush rakhe.",
    "Good neighbours are rare, glad we have one.",
    "Will ask again when I need something.",
    "",
    "",
]
_NEU_OPEN = [
    "Okay experience overall.",
    "Theek tha, bas thori der ho gayi.",
    "Fine, but communication could be better.",
    "Average, nothing special.",
    "Not bad, not great either.",
    "Kaam chal gaya, bas.",
    "Decent, with a couple of small hiccups.",
    "Got what I needed in the end.",
]
_NEU_DETAIL = [
    "The {item} came back a few hours late.",
    "Had to remind them twice about the return.",
    "{item} was returned a bit dirty.",
    "Late reply but sorted in the end.",
    "Pickup was delayed by an hour for no clear reason.",
    "Cord was tangled and one accessory was missing at first, found it later.",
    "Return aaj ke bajaye kal hua.",
    "The {item} needed a quick wipe-down before I could reuse it.",
]
_NEG_OPEN = [
    "Not happy with this one.",
    "Mujhe afsos hai, tajurba acha nahi raha.",
    "Would think twice before lending again.",
    "Disappointed.",
]
_NEG_DETAIL = [
    "The {item} was returned with damage.",
    "{item} bohat late wapis kiya aur batana bhi zaroori nahi samjha.",
    "The {item} did not match the description.",
    "Very slow replies and the return kept getting pushed back.",
    "I had to follow up many times about the {item}.",
    "A part of the {item} went missing and nobody said sorry.",
    "Pehle se bataya hota to main kuch aur bandobast kar leta.",
    "The {item} smelled of smoke and had stains that were not there before.",
    "Rude tone when I asked about the {item}.",
]


def legit_review(rng: random.Random, quality: str, item: str) -> str:
    """quality: 'good' | 'ok' | 'bad'. Two or three random parts, so texts differ."""
    if quality == "good":
        parts = [rng.choice(_POS_OPEN), rng.choice(_POS_DETAIL), rng.choice(_POS_CLOSE)]
        if rng.random() < 0.35:
            parts.pop(0)
    elif quality == "ok":
        parts = [rng.choice(_NEU_OPEN), rng.choice(_NEU_DETAIL)]
        if rng.random() < 0.4:
            parts.append(rng.choice(_POS_CLOSE))
    else:
        parts = [rng.choice(_NEG_OPEN), rng.choice(_NEG_DETAIL)]
    if quality != "good" and rng.random() < 0.2:
        rng.shuffle(parts)
    text = " ".join(p.format(item=item.lower()) for p in parts if p)
    return text.strip()


# ---------------------------------------------------------------- attack reviews (development set)

_RING_BASE = "Highly trustworthy and reliable person! Highly recommended!"
_RING_TAILS = ["", " 5 stars!", " Best neighbour!", " Totally recommended!", " A+ !!"]


def ring_review(rng: random.Random) -> str:
    """Near-identical praise: the 'highly similar reviews' signal."""
    return _RING_BASE + rng.choice(_RING_TAILS)


_FARM_BASE = "Excellent lender, very trustworthy, item was perfect, will definitely borrow again"
_FARM_TAILS = [".", "!", " 100%.", " for sure.", "!!"]


def farm_review(rng: random.Random) -> str:
    return _FARM_BASE + rng.choice(_FARM_TAILS)


_BURST_BASE = "Very reliable person, quick and smooth deal, thanks"
_BURST_TAILS = ["!", ".", " a lot!", "!!", " :)"]


def burst_review(rng: random.Random) -> str:
    return _BURST_BASE + rng.choice(_BURST_TAILS)


def retaliation_review(rng: random.Random, item: str) -> str:
    return rng.choice(
        [
            f"Terrible lender, the {item.lower()} was not as described and they were rude.",
            f"Do not lend to or borrow from this person. The {item.lower()} was a mess.",
            "Worst experience, unfair and unresponsive. Stay away.",
        ]
    )


# ---------------------------------------------------------------- disputes, messages, notes

_DISPUTE_DESC = {
    "DAMAGE": [
        "The {item} came back with a crack that was not there at handover.",
        "{item} returned with a broken part; borrower says it was already like that.",
        "There is visible damage on the {item}, photos attached to the checklist.",
    ],
    "NON_RETURN": [
        "The {item} has not been returned {n} days after the agreed date.",
        "Borrower stopped replying and the {item} is still with them.",
    ],
    "CONDITION_MISMATCH": [
        "The {item} was not in the condition described in the listing.",
        "{item} did not work properly at handover, which the listing did not mention.",
    ],
    "NO_SHOW": ["Borrower did not turn up for the handover of the {item}."],
    "OTHER": ["Disagreement about the agreed terms for the {item}."],
}


def dispute_description(rng: random.Random, reason: str, item: str, n: int = 4) -> str:
    return rng.choice(_DISPUTE_DESC[reason]).format(item=item.lower(), n=n)


_DECISION = {
    "borrower": [
        "Evidence supports the lender's claim; recorded against the borrower.",
        "Handover and return checklists differ; borrower responsible.",
    ],
    "lender": [
        "Listing did not match the item; recorded against the lender.",
        "Claim not supported by the handover checklist; borrower cleared.",
    ],
    "none": [
        "Evidence inconclusive; no fault recorded for either party.",
        "Both parties agreed the matter was a misunderstanding; no fault recorded.",
    ],
}


def decision_reason(rng: random.Random, fault: str) -> str:
    return rng.choice(_DECISION[fault])


_MESSAGES = [
    "Need it for the weekend, will take good care of it.",
    "Could I borrow this for a few days?",
    "Chahiye tha ek do din ke liye, shukriya.",
    "Short project at home, will return on time.",
    "Family function this week, would really help.",
    "Is it available around the dates below?",
    "",
    "",
]


def request_message(rng: random.Random) -> str:
    return rng.choice(_MESSAGES)


_COND_OK = ["Checked together, all fine.", "Working and clean.", "Looks as described.", ""]
_COND_BAD = [
    "Visible damage noted.",
    "Not as described.",
    "Missing a part.",
    "Condition differs from handover.",
]


def condition_note(rng: random.Random, ok: bool) -> str | None:
    t = rng.choice(_COND_OK if ok else _COND_BAD)
    return t or None


_DECLINE = ["not_available", "not_comfortable", "dates_taken", "other"]


def decline_reason(rng: random.Random) -> str:
    return rng.choice(_DECLINE)


FIRST_NAMES = [
    "Ali",
    "Zara",
    "Imran",
    "Hina",
    "Fatima",
    "Ahmed",
    "Ayesha",
    "Bilal",
    "Sana",
    "Usman",
    "Nadia",
    "Hassan",
    "Maryam",
    "Kamran",
    "Saima",
    "Tariq",
    "Rabia",
    "Faisal",
    "Shazia",
    "Adnan",
    "Lubna",
    "Waqas",
    "Amna",
    "Kashif",
    "Iqra",
    "Shahid",
    "Razia",
    "Nawaz",
    "Bushra",
    "Asad",
    "Sobia",
    "Hamid",
    "Faiza",
    "Rehan",
    "Mehwish",
    "Saad",
    "Gulnaz",
    "Rizwan",
    "Tahira",
    "Junaid",
    "Samina",
    "Zubair",
    "Naila",
    "Irfan",
    "Afshan",
    "Danish",
    "Rozina",
    "Ehsan",
    "Shabana",
    "Waseem",
    "Arooj",
    "Nasir",
    "Kiran",
    "Rashid",
    "Parveen",
    "Arslan",
    "Sumaira",
    "Mohsin",
    "Zehra",
    "Ahsan",
]
SURNAMES = [
    "Khan",
    "Malik",
    "Qureshi",
    "Butt",
    "Chaudhry",
    "Sheikh",
    "Mirza",
    "Siddiqui",
    "Raza",
    "Akhtar",
    "Hashmi",
    "Baig",
    "Rana",
    "Cheema",
    "Gillani",
    "Lodhi",
    "Niazi",
    "Awan",
    "Javed",
    "Zaidi",
]
