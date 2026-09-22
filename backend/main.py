import os
import re
import math
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="You Are 1 Among Them API")
configured_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", *configured_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARCHETYPES = {
    "mischievous": "mischievous playful trouble",
    "chaotic": "chaotic impulsive unpredictable hyperactive",
    "lonely": "lonely helpless escapist wants someone to save",
    "overconfident": "unbothered confidence swagger larger than life",
    "heroic": "heroic loyal protective determined refuses to give up",
    "revenge_driven": "revenge driven ruthless intimidating",
    "romantic": "romantic charming dramatic emotionally intense",
    "one_sided_love": "loving someone who loves another person; unrequited, one-sided romantic love and heartbreak",
    "good_boy": "a teasing, wholesome good-boy persona; well-behaved, obedient, innocent, teacher's-pet energy",
    "philosophical": "philosophical wise calm reflective",
    "power_hungry": "power hungry dominant territorial ambitious",
    "adventurous": "adventurous curious energetic exploring",
    "reality_manipulator": "reality manipulator universes impossible",
    "time_manipulator": "time manipulator timelines time travel",
    "genius": "genius futuristic unconventional obsessed with building",
    "antihero": "antihero morally complicated dark clever",
    "dumbass": "dumbass foolish reckless silly, fooled always and goofy",
    "kind": "kind compassionate helpful",
    "persevering": "persevering determined persistent",
    "depressed": "depressed sad hopeless withdrawn",
    "lovable": "lovable endearing charming",
    "swag": "swag stylish confident cool",
    "composed": "composed calm collected serene",
    "cry_baby": "sensitive, emotionally overwhelmed, and easily upset",
    "opportunistic": "switches toward whoever benefits them, usually in a negative or self-serving way",
    "social_chameleon": "adaptable and able to blend into different social situations",
    "oblivious": "oblivious unaware inattentive",
    "ambitious": "ambitious, driven, and goal-oriented",
    "blushing": "blushing embarrassed shy",
    "single": "single independent unattached",
    "undercover": "working on a secret mission, intelligence operation, or covert assignment",
    "patriotic": "driven to serve, protect, improve, or act for their country or nation; national duty, homeland, public service",
    "unyielding": "unyielding determined persistent , completely solid and hard, or firmly refusing to change your mind, plans, or behavior"
}

CHARACTER_TAGS = {
    "nobita": ["kind", "cry_baby", "dumbass"], 
    "naruto": ["heroic", "adventurous", "unyielding"], 
    "spider-man": ["heroic", "mischievous", "chaotic"],
    "salman-khan": ["heroic", "swag", "single"],
    "salman-khan-ceo": ["ambitious", "swag", "overconfident"],
    "salman-khan-sad": ["depressed", "cry_baby", "single"],
    "dhurandar": ["genius", "undercover", "patriotic"],
    "ajit-doval": ["genius", "philosophical"], 
    "elon-musk": ["genius", "adventurous", "power_hungry", "ambitious"],
    "ishowspeed": ["chaotic", "adventurous"],
    "speed-hmmm": ["chaotic", "blushing"],
    "loki": ["mischievous", "chaotic", "power_hungry", "time_manipulator"],
    "srk": ["romantic", "overconfident"], 
    "max-verstappen": ["unyielding", "genius", "adventurous"],
    "pr": ["depressed", "swag", "chaotic"],
    "uzair-baloch": ["dumbass"],
    "mufasa": ["philosophical", "heroic"], 
    "rajinikanth": ["heroic", "swag"],
    "lewis-hamilton": ["heroic", "genius", "composed"],
    "peter-parker": ["depressed", "lovable"],
    "suzuka": ["social_chameleon", "opportunistic"],
    "arjun": ["depressed"],
    "arjun-trying": ["unyielding", "persevering", "ambitious", "heroic"],
    "jd": ["depressed", "kind", "oblivious"],
    "jd-sad": ["depressed", "cry_baby"],
    "anuskha-sharma": ["romantic", "lovable", "composed"],
    "barfi": ["lovable", "kind", "romantic"],
    "doreamon-acha-loude": ["kind", "lovable", "chaotic"],
    "leo-das": ["antihero", "revenge_driven", "power_hungry"],
    "parthiban": ["composed", "antihero", "philosophical"],
    "ash": ["unyielding", "ambitious"],
    "vasanth-1": ["good_boy"],
    "vasanth-2": ["good_boy"],
    "vasanth-3": ["good_boy"]
}

EXCLUSIVE_CHARACTER_GROUPS = {
    "good_boy": ["vasanth-1", "vasanth-2", "vasanth-3"],
}


class ClassifyRequest(BaseModel):
    input: str


def is_one_sided_love(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "one sided love",
        "one-sided love",
        "unrequited love",
        "loves someone else",
        "love someone else",
        "doesn't love me back",
        "does not love me back",
    )
    return any(phrase in lowered for phrase in phrases) or (
        "love" in lowered
        and ("someone else" in lowered or "another person" in lowered)
    )


def is_good_boy_intent(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "good boy",
        "good-boy",
        "well behaved",
        "well-behaved",
        "teacher's pet",
        "teachers pet",
        "obedient boy",
    )
    return any(phrase in lowered for phrase in phrases)


def fallback_classify(text: str) -> dict[str, Any]:
    if is_one_sided_love(text):
        return {
            "categories": [{"id": "one_sided_love", "probability": 1.0}],
            "characters": ["pr"],
            "mode": "one_sided_love",
            "source": "local fallback",
        }
    if is_good_boy_intent(text):
        return {
            "categories": [{"id": "good_boy", "probability": 1.0}],
            "characters": EXCLUSIVE_CHARACTER_GROUPS["good_boy"],
            "mode": "good_boy",
            "source": "local fallback",
        }
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    scores = []
    for archetype, words in ARCHETYPES.items():
        keywords = re.findall(r"[a-z]+", words.lower())
        hits = sum(word in tokens for word in keywords if len(word) > 3)
        # Keep unrelated archetypes near zero; the fallback must not invent a
        # strong match merely because the input length happens to line up.
        nudge = ((len(text) * (len(archetype) + 3)) % 5) / 100
        scores.append({"id": archetype, "probability": min(0.96, hits * 0.22 + nudge)})
    # The local fallback should understand the product's most important
    # semantic cue even without a TypeSafe key.
    if tokens.intersection({"country", "nation", "homeland", "patriot", "patriotic"}):
        score_by_id = {item["id"]: item for item in scores}
        score_by_id["patriotic"]["probability"] = 0.92
        score_by_id["undercover"]["probability"] = max(score_by_id["undercover"]["probability"], 0.68)
    categories = sorted(scores, key=lambda item: item["probability"], reverse=True)[:5]
    selected = select_characters({item["id"]: item["probability"] for item in scores})
    return {"categories": categories, "characters": selected, "source": "local fallback"}


def select_characters(probabilities: dict[str, float]) -> list[str]:
    """Rank by probability-weighted tag relevance without character-specific rules.

    Dividing by the square root of a character's tag count prevents a character
    with many weak, unrelated tags from beating a character with one very
    strong matching tag. This keeps matching data-driven while still allowing
    characters to have several possible archetypes.
    """
    scored = []
    for character, tags in CHARACTER_TAGS.items():
        weighted_score = sum(probabilities.get(tag, 0.0) for tag in tags)
        specificity = math.sqrt(max(len(tags), 1))
        matching_tags = sum(probabilities.get(tag, 0.0) > 0.05 for tag in tags)
        scored.append((character, weighted_score / specificity, matching_tags))
    scored.sort(key=lambda item: (item[1], item[2]), reverse=True)
    return [character for character, _, _ in scored[:5]]


async def typesafe_classify(text: str) -> dict[str, Any]:
    payload = {
        "model": "jev-latest",
        "state": text,
        "questions": {
            "archetype": {
                "type": "choice",
                "instructions": "Choose the single archetype that best captures the user's current emotional or imagined state. Only choose from the provided categories. Prefer the closest semantic match, not a literal keyword match.",
                "criteria": ARCHETYPES,
            },
            "country_mission": {
                "type": "noul",
                "instructions": "Does the user express wanting to do something for, to, or on behalf of their country or nation?",
                "criteria": {
                    "true": "The user expresses national duty, serving or protecting their country, improving their nation, or acting on its behalf.",
                    "false": "No country, nation, homeland, or national-duty intent is expressed.",
                },
            },
            "one_sided_love": {
                "type": "noul",
                "instructions": "Does the user describe loving someone who loves another person, or romantic feelings that are not returned?",
                "criteria": {
                    "true": "The user describes one-sided, unrequited, or not-returned romantic love.",
                    "false": "The user is not describing unreturned romantic love.",
                },
            },
            "good_boy_intent": {
                "type": "noul",
                "instructions": "Is the user teasingly describing a wholesome, well-behaved, obedient, innocent good-boy persona?",
                "criteria": {
                    "true": "The user is clearly invoking good-boy, well-behaved, obedient, or teacher's-pet energy.",
                    "false": "The user is not describing that teasing good-boy persona.",
                },
            },
        },
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.typesafe.ai/v1/systemone",
            headers={"Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}"},
            json=payload,
        )
    if response.is_error:
        raise HTTPException(status_code=502, detail=f"TypeSafe returned {response.status_code}")
    answer = response.json().get("answers", {}).get("archetype", {})
    categories = sorted(
        [{"id": key, "probability": value} for key, value in answer.get("probabilities", {}).items()],
        key=lambda item: item["probability"],
        reverse=True,
    )[:5]
    probabilities = dict(answer.get("probabilities", {}))
    country_signal = response.json().get("answers", {}).get("country_mission", {}).get("noul", 0.0)
    one_sided_signal = response.json().get("answers", {}).get("one_sided_love", {}).get("noul", 0.0)
    good_boy_signal = response.json().get("answers", {}).get("good_boy_intent", {}).get("noul", 0.0)
    if one_sided_signal >= 0.7:
        return {
            "categories": [{"id": "one_sided_love", "probability": one_sided_signal}, *categories[:4]],
            "characters": ["pr"],
            "mode": "one_sided_love",
            "source": "jev-latest",
        }
    if good_boy_signal >= 0.7:
        return {
            "categories": [{"id": "good_boy", "probability": good_boy_signal}, *categories[:4]],
            "characters": EXCLUSIVE_CHARACTER_GROUPS["good_boy"],
            "mode": "good_boy",
            "source": "jev-latest",
        }
    if country_signal >= 0.55:
        probabilities["patriotic"] = max(probabilities.get("patriotic", 0.0), country_signal)
        probabilities["undercover"] = max(probabilities.get("undercover", 0.0), country_signal * 0.82)
    selected = select_characters(probabilities)
    return {"categories": categories, "characters": selected, "source": "jev-latest"}


@app.post("/classify")
@app.post("/api/classify")
async def classify(request: ClassifyRequest):
    text = request.input.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Please describe how you feel.")
    if os.getenv("TYPESAFE_API_KEY"):
        return await typesafe_classify(text)
    return fallback_classify(text)
