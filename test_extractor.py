from fact_extract import fact_extractor


test_cases = [
    "Tokyo's population in 2020 was approximately 14 million people.",
    "The Eiffel Tower is 330 meters tall and was built in 1889.",
    "Apple Inc. was founded by Steve Jobs in 1976 in California.",
    "The price of gold reached $2000 per ounce in 2020.",
]


for i, text in enumerate(test_cases, 1):
    print(f"\n{'=' * 60}")
    print(f"Test Case {i}: {text}")
    print(f"{'=' * 60}")
    
    facts = fact_extractor.extract_facts(text)
    
    if not facts:
        print("\nNo facts extracted.")
        continue
    
    for j, fact in enumerate(facts, 1):
        print(f"\nFact {j}:")
        print(f"  Entity: {fact['entity']}")
        print(f"  Type: {fact['entity_type']}")
        print(f"  Fact Type: {fact.get('fact_type', 'N/A')}")
        print(f"  Sentence: {fact['sentence']}")