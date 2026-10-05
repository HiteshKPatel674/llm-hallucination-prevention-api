from refdatabase import wikipedia_verifier


test_facts = [
    {
        "entity": "Tokyo",
        "entity_type": "GPE",
        "sentence": "Tokyo's population in 2020 was 14 million",
        "claim": "Tokyo's population in 2020 was 14 million"
    },
    {
        "entity": "14 million",
        "entity_type": "POPULATION",
        "sentence": "Tokyo's population in 2020 was 14 million",
        "claim": "Tokyo's population in 2020 was 14 million"
    },
    {
        "entity": "Eiffel Tower",
        "entity_type": "LOC",
        "sentence": "The Eiffel Tower is 330 meters tall",
        "claim": "The Eiffel Tower is 330 meters tall"
    },
    {
        "entity": "330 meters",
        "entity_type": "MEASUREMENT",
        "sentence": "The Eiffel Tower is 330 meters tall",
        "claim": "The Eiffel Tower is 330 meters tall"
    }
]


print("Testing Wikipedia Verification\n")
print("=" * 70)


for i, fact in enumerate(test_facts, 1):

    print(f"\nTest Case {i}")
    print("-" * 70)

    print("Original Fact:")
    print(f"  Entity: {fact['entity']}")
    print(f"  Type: {fact['entity_type']}")
    print(f"  Sentence: {fact['sentence']}")

    verified = wikipedia_verifier.verify_fact(fact)

    print("\nVerification Result:")
    print(f"  Verified: {verified['verified']}")
    print(f"  Confidence: {verified['confidence']}")
    print(f"  Note: {verified['verification_note']}")

    if verified.get("wikipedia_url"):
        print(f"  URL: {verified['wikipedia_url']}")

    if verified.get("wikipedia_title"):
        print(f"  Wikipedia Title: {verified['wikipedia_title']}")

    print("-" * 70)