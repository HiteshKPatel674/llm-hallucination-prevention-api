from response_formatter import response_formatter


test_text = (
    "Tokyo is the capital of Japan with a population "
    "of 14 million people. The city was founded in 1457."
)


test_facts = [
    {
        "entity": "Tokyo",
        "entity_type": "GPE",
        "verified": True,
        "confidence": "high",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Tokyo",
        "verification_note": "Entity found in Wikipedia"
    },
    {
        "entity": "Japan",
        "entity_type": "GPE",
        "verified": True,
        "confidence": "high",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Japan",
        "verification_note": "Entity found in Wikipedia"
    },
    {
        "entity": "14 million",
        "entity_type": "CARDINAL",
        "verified": True,
        "confidence": "medium",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Tokyo",
        "verification_note": "Similar value found in Wikipedia"
    },
    {
        "entity": "1457",
        "entity_type": "DATE",
        "verified": False,
        "confidence": "low",
        "wikipedia_url": None,
        "verification_note": "Value not found in Wikipedia"
    }
]


test_contradictions = []


print("Testing Response Formatter\n")
print("=" * 70)


result = response_formatter.format_response(
    test_text,
    test_facts,
    test_contradictions
)


print("\n📄 ORIGINAL:")
print(result["original"])


print("\n📊 FACT SUMMARY:")

for i, fact in enumerate(result["facts"], 1):
    print(f"\n  Fact {i}:")
    print(f"    Entity: {fact['entity']}")
    print(f"    Type: {fact['type']}")
    print(f"    Status: {fact['status']}")
    print(f"    Verified: {fact['verified']}")
    print(f"    Confidence: {fact['confidence']}")
    print(f"    Note: {fact['note']}")


print("\n🚨 CONTRADICTIONS:")
print(f"  {len(result['contradictions'])} contradiction(s)")


print("\n⚠️ HAS ISSUES:")
print(f"  {result['has_issues']}")


print("\n" + "=" * 70)
print("Response formatting test completed.")