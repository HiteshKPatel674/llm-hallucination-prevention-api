from contradiction_detector import contradiction_detector


print("Testing Contradiction Detection\n")
print("=" * 70)

session_id = "test_session"


# Message 1
print("\n📝 Message 1: 'Tokyo has 14 million people'")

facts_1 = [
    {
        "entity": "Tokyo",
        "entity_type": "GPE",
        "sentence": "Tokyo has 14 million people",
        "claim": "Tokyo has 14 million people"
    },
    {
        "entity": "14 million",
        "entity_type": "POPULATION",
        "sentence": "Tokyo has 14 million people",
        "claim": "Tokyo has 14 million people"
    }
]

contradictions = contradiction_detector.detect_contradictions(
    session_id,
    facts_1
)

print(f"Contradictions found: {len(contradictions)}")

contradiction_detector.add_facts(
    session_id,
    facts_1
)


# Message 2
print("\n📝 Message 2: 'Tokyo has 38 million people'")

facts_2 = [
    {
        "entity": "Tokyo",
        "entity_type": "GPE",
        "sentence": "Tokyo has 38 million people",
        "claim": "Tokyo has 38 million people"
    },
    {
        "entity": "38 million",
        "entity_type": "POPULATION",
        "sentence": "Tokyo has 38 million people",
        "claim": "Tokyo has 38 million people"
    }
]

contradictions = contradiction_detector.detect_contradictions(
    session_id,
    facts_2
)

print(f"Contradictions found: {len(contradictions)}")

if contradictions:
    print("\n🚨 CONTRADICTION DETECTED:")
    
    for i, cont in enumerate(contradictions, 1):
        print(f"\n  Contradiction {i}:")
        print(f"    Type: {cont['type']}")
        print(f"    Severity: {cont['severity']}")
        print(f"    Previous: {cont['previous_value']}")
        print(f"    Current: {cont['current_value']}")
        print(f"    Difference: {cont['difference']}")
        print(f"    Message: {cont['message']}")

contradiction_detector.add_facts(
    session_id,
    facts_2
)


# Message 3
print("\n📝 Message 3: 'The Eiffel Tower is 330 meters tall'")

facts_3 = [
    {
        "entity": "Eiffel Tower",
        "entity_type": "LOC",
        "sentence": "The Eiffel Tower is 330 meters tall",
        "claim": "The Eiffel Tower is 330 meters tall"
    }
]

contradictions = contradiction_detector.detect_contradictions(
    session_id,
    facts_3
)

print(f"Contradictions found: {len(contradictions)}")

contradiction_detector.add_facts(
    session_id,
    facts_3
)


# Summary
print("\n" + "=" * 70)

summary = contradiction_detector.get_session_summary(
    session_id
)

print("\nSession Summary:")
print(f"  Total facts tracked: {summary['total_facts']}")

contradiction_detector.clear_session(session_id)