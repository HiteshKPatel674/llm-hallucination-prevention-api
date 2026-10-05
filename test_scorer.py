from confidence_scorer import confidence_scorer


test_facts_high = [
    {
        "entity": "Tokyo",
        "entity_type": "GPE",
        "verified": True,
        "confidence": "high"
    },
    {
        "entity": "14 million",
        "entity_type": "CARDINAL",
        "verified": True,
        "confidence": "high"
    },
    {
        "entity": "2020",
        "entity_type": "DATE",
        "verified": True,
        "confidence": "high"
    }
]


test_facts_medium = [
    {
        "entity": "Paris",
        "entity_type": "GPE",
        "verified": True,
        "confidence": "high"
    },
    {
        "entity": "2.2 million",
        "entity_type": "CARDINAL",
        "verified": True,
        "confidence": "medium"
    },
    {
        "entity": "unknown city",
        "entity_type": "GPE",
        "verified": False,
        "confidence": "unknown"
    }
]


test_facts_low = [
    {
        "entity": "Fake City",
        "entity_type": "GPE",
        "verified": False,
        "confidence": "low"
    },
    {
        "entity": "999 billion",
        "entity_type": "CARDINAL",
        "verified": False,
        "confidence": "low"
    }
]


test_cases = [
    (test_facts_high, "High Confidence"),
    (test_facts_medium, "Medium Confidence"),
    (test_facts_low, "Low Confidence")
]


print("Testing Confidence Scorer\n")
print("=" * 70)


for i, (test_facts, label) in enumerate(test_cases, 1):

    print(f"\nTest Case {i}: {label}")
    print("-" * 70)

    result = confidence_scorer.score_response(test_facts)

    print(
        f"{result['emoji']} "
        f"Overall Confidence: "
        f"{result['overall_confidence'].upper()}"
    )

    print(
        f"Score: "
        f"{result['confidence_score']}/1.0"
    )

    print(
        f"Color: "
        f"{result['color']}"
    )

    print(
        f"Summary: "
        f"{result['summary']}"
    )

    print("\nStats:")

    print(
        f"  Total Facts: "
        f"{result['stats']['total_facts']}"
    )

    print(
        f"  Verified: "
        f"{result['stats']['verified']}"
    )

    print(
        f"  Unverified: "
        f"{result['stats']['unverified']}"
    )

    print(
        f"  Unknown: "
        f"{result['stats']['unknown']}"
    )

    print("=" * 70)