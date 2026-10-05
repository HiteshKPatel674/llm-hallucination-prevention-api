import spacy
import re
from typing import List, Dict, Optional


try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None


class FactExtractor:

    def __init__(self):
        self.nlp = nlp

    def extract_facts(
        self,
        text: str
    ) -> List[Dict]:

        if not self.nlp or not text.strip():
            return []

        text = self._clean_text(text)

        if not text:
            return []

        facts = []

        doc = self.nlp(text)

        for sent in doc.sents:

            sentence = sent.text.strip()

            if not sentence:
                continue

            structured_claim = (
                self._extract_structured_claim(
                    sentence
                )
            )

            if structured_claim:

                facts.append({
                    "claim": sentence,
                    "sentence": sentence,
                    "subject": structured_claim["subject"],
                    "relation": structured_claim["relation"],
                    "value": structured_claim["value"],
                    "aliases": structured_claim.get(
                        "aliases",
                        []
                    ),
                    "entity": structured_claim["value"],
                    "entity_type": structured_claim[
                        "entity_type"
                    ],
                    "fact_type": structured_claim[
                        "relation"
                    ]
                })

                continue

            entities = []

            for ent in sent.ents:

                entity = ent.text.strip()

                if not self._is_valid_entity(
                    entity,
                    ent.label_
                ):
                    continue

                entities.append(ent)

            if entities:

                primary_entity = (
                    self._select_primary_entity(
                        entities
                    )
                )

                facts.append({
                    "claim": sentence,
                    "sentence": sentence,
                    "subject": None,
                    "relation": None,
                    "value": primary_entity.text.strip(),
                    "aliases": [],
                    "entity": primary_entity.text.strip(),
                    "entity_type": primary_entity.label_,
                    "fact_type": self._get_fact_type(
                        primary_entity.label_
                    )
                })

        numeric_facts = (
            self._extract_numeric_facts(
                text
            )
        )

        facts.extend(
            numeric_facts
        )

        date_facts = (
            self._extract_date_patterns(
                text
            )
        )

        facts.extend(
            date_facts
        )

        return self._remove_duplicates(
            facts
        )

    # ==================================================
    # STRUCTURED CLAIM EXTRACTION
    # ==================================================

    def _extract_structured_claim(
        self,
        sentence: str
    ) -> Optional[Dict]:

        patterns = [

            # The currency of India is the Indian Rupee.
            (
                r"the\s+currency\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "currency",
                "normal"
            ),

            # The capital of Japan is Tokyo.
            (
                r"the\s+capital\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "capital",
                "normal"
            ),

            # The population of India is 1.4 billion.
            (
                r"the\s+population\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "population",
                "normal"
            ),

            # The area of India is ...
            (
                r"the\s+area\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "area",
                "normal"
            ),

            # The official language of India is Hindi.
            (
                r"the\s+official\s+language(?:s)?\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "official_language",
                "normal"
            ),

            # The largest city of India is Mumbai.
            (
                r"the\s+largest\s+city\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "largest_city",
                "normal"
            ),

            # The founder of Microsoft is Bill Gates.
            (
                r"the\s+founder\s+of\s+(.+?)"
                r"\s+is\s+(.+)",
                "founder",
                "normal"
            ),

            # The headquarters of Microsoft is in Redmond.
            (
                r"the\s+headquarters\s+of\s+(.+?)"
                r"\s+is\s+(?:in\s+)?(.+)",
                "headquarters",
                "normal"
            ),

            # Tokyo is the capital of Japan.
            (
                r"(.+?)\s+is\s+the\s+capital\s+of\s+(.+)",
                "capital",
                "reverse"
            ),

            # The Indian Rupee is the currency of India.
            (
                r"(.+?)\s+is\s+the\s+currency\s+of\s+(.+)",
                "currency",
                "reverse"
            ),

            # Hindi is the official language of India.
            (
                r"(.+?)\s+is\s+the\s+official\s+language"
                r"(?:\s+of)?\s+(.+)",
                "official_language",
                "reverse"
            ),

            # Mumbai is the largest city of India.
            (
                r"(.+?)\s+is\s+the\s+largest\s+city\s+of\s+(.+)",
                "largest_city",
                "reverse"
            ),

            # Bill Gates is the founder of Microsoft.
            (
                r"(.+?)\s+is\s+the\s+founder\s+of\s+(.+)",
                "founder",
                "reverse"
            )
        ]

        for pattern, relation, direction in patterns:

            match = re.search(
                pattern,
                sentence,
                re.IGNORECASE
            )

            if not match:
                continue

            if direction == "normal":

                subject = (
                    match.group(1)
                    .strip()
                )

                raw_value = (
                    match.group(2)
                    .strip()
                )

            else:

                raw_value = (
                    match.group(1)
                    .strip()
                )

                subject = (
                    match.group(2)
                    .strip()
                )

            subject = self._clean_entity_text(
                subject
            )

            value = self._clean_value(
                raw_value
            )

            aliases = (
                self._extract_value_aliases(
                    raw_value
                )
            )

            return {
                "subject": subject,
                "relation": relation,
                "value": value,
                "aliases": aliases,
                "entity_type": self._relation_entity_type(
                    relation
                )
            }

        return None

    def _clean_entity_text(
        self,
        text: str
    ) -> str:

        text = re.sub(
            r"[.!?]+$",
            "",
            text
        )

        text = re.sub(
            r"^(the|a|an)\s+",
            "",
            text,
            flags=re.IGNORECASE
        )

        return text.strip()

    def _clean_value(
        self,
        value: str
    ) -> str:

        value = re.sub(
            r"[.!?]+$",
            "",
            value
        ).strip()

        # Remove "abbreviated as INR"
        value = re.sub(
            r",?\s+"
            r"(?:abbreviated|shortened)"
            r"(?:\s+as)?\s+"
            r"[A-Za-z0-9₹$€£-]+$",
            "",
            value,
            flags=re.IGNORECASE
        )

        # Remove "also known as ..."
        value = re.sub(
            r",?\s+"
            r"(?:also\s+known\s+as|known\s+as)"
            r"\s+.+$",
            "",
            value,
            flags=re.IGNORECASE
        )

        value = re.sub(
            r"^(the|a|an)\s+",
            "",
            value,
            flags=re.IGNORECASE
        )

        return value.strip()

    def _extract_value_aliases(
        self,
        value: str
    ) -> List[str]:

        aliases = []

        patterns = [

            r"(?:abbreviated|shortened)"
            r"\s+(?:as)?\s*"
            r"([A-Za-z0-9₹$€£-]+)",

            r"(?:also\s+known\s+as|known\s+as)"
            r"\s+(.+)"
        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                value,
                flags=re.IGNORECASE
            )

            for alias in matches:

                alias = re.sub(
                    r"[.!?]+$",
                    "",
                    alias
                ).strip()

                if (
                    alias
                    and alias.lower()
                    not in [
                        "as",
                        "the"
                    ]
                ):

                    aliases.append(
                        alias
                    )

        return list(
            dict.fromkeys(
                aliases
            )
        )

    def _relation_entity_type(
        self,
        relation: str
    ) -> str:

        mapping = {

            "currency": "CURRENCY",

            "capital": "LOCATION",

            "population": "NUMBER",

            "area": "MEASUREMENT",

            "official_language": "LANGUAGE",

            "largest_city": "LOCATION",

            "founder": "PERSON",

            "headquarters": "LOCATION"
        }

        return mapping.get(
            relation,
            "GENERAL"
        )

    # ==================================================
    # GENERAL ENTITY EXTRACTION
    # ==================================================

    def _select_primary_entity(
        self,
        entities
    ):

        for ent in entities:

            if ent.root.dep_ in [
                "nsubj",
                "nsubjpass"
            ]:

                return ent

        preferred_types = [
            "PERSON",
            "ORG",
            "GPE",
            "LOC"
        ]

        for entity_type in preferred_types:

            for ent in entities:

                if ent.label_ == entity_type:

                    return ent

        return entities[0]

    def _is_valid_entity(
        self,
        entity: str,
        entity_type: str
    ) -> bool:

        cleaned = entity.strip(
            "#*-_ "
        )

        if not cleaned:
            return False

        if len(cleaned) < 2:
            return False

        if entity_type == "MONEY":

            if not re.search(
                r"[$₹€£]\s*[\d,.]+",
                entity
            ):
                return False

        if entity_type == "CARDINAL":

            if not re.search(
                r"\d",
                entity
            ):
                return False

        if entity_type == "DATE":

            if not re.search(
                r"\d",
                entity
            ):
                return False

        return True

    def _get_fact_type(
        self,
        entity_type: str
    ) -> str:

        mapping = {

            "PERSON": "PERSON",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "ORG": "ORGANIZATION",
            "DATE": "DATE",
            "TIME": "TIME",
            "MONEY": "MONEY",
            "QUANTITY": "QUANTITY",
            "CARDINAL": "NUMBER"
        }

        return mapping.get(
            entity_type,
            "GENERAL"
        )

    # ==================================================
    # NUMERIC FACTS
    # ==================================================

    def _extract_numeric_facts(
        self,
        text: str
    ) -> List[Dict]:

        facts = []

        patterns = [

            (
                r"([\d,.]+\s*"
                r"(?:million|billion|trillion|"
                r"thousand|hundred)"
                r"(?:\s+people)?)",
                "POPULATION"
            ),

            (
                r"([$₹€£]\s?"
                r"[\d,.]+"
                r"(?:\s*(?:million|billion|thousand))?)",
                "MONEY"
            ),

            (
                r"([\d,.]+\s*(?:%|percent))",
                "PERCENTAGE"
            ),

            (
                r"([\d,.]+\s*"
                r"(?:meters?|metres?|feet|foot|"
                r"kilometers?|kilometres?|miles?|"
                r"km|ft|mi))",
                "MEASUREMENT"
            ),

            (
                r"([\d,.]+\s*"
                r"(?:kg|kgs|kilograms?|tons?|"
                r"tonnes?|pounds?|lbs?|grams?|g))",
                "WEIGHT"
            ),

            (
                r"([\d,.]+\s*"
                r"(?:degrees?|°)\s*[CF]?)",
                "TEMPERATURE"
            ),

            (
                r"([\d,.]+\s*"
                r"(?:km/h|kmph|mph|"
                r"meters per second|m/s))",
                "SPEED"
            ),

            (
                r"([\d,.]+\s*"
                r"(?:square kilometers?|"
                r"square miles?|km²|mi²|"
                r"sq\.?\s*km))",
                "AREA"
            )
        ]

        for pattern, fact_type in patterns:

            matches = re.finditer(
                pattern,
                text,
                re.IGNORECASE
            )

            for match in matches:

                sentence = (
                    self._get_text_sentence(
                        text,
                        match.start(),
                        match.end()
                    )
                )

                facts.append({
                    "claim": sentence,
                    "sentence": sentence,
                    "subject": None,
                    "relation": None,
                    "value": match.group(1).strip(),
                    "aliases": [],
                    "entity": match.group(1).strip(),
                    "entity_type": fact_type,
                    "fact_type": fact_type
                })

        return facts

    # ==================================================
    # DATE FACTS
    # ==================================================

    def _extract_date_patterns(
        self,
        text: str
    ) -> List[Dict]:

        facts = []

        patterns = [

            (
                r"(?:in|during|since|from|after|before)"
                r"\s+(\d{4})",
                "DATE"
            ),

            (
                r"(?:established|built|founded|"
                r"created|born|died|launched|invented)"
                r"\s+(?:in\s+)?(\d{4})",
                "DATE"
            ),

            (
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                "DATE"
            ),

            (
                r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
                "DATE"
            )
        ]

        for pattern, fact_type in patterns:

            matches = re.finditer(
                pattern,
                text,
                re.IGNORECASE
            )

            for match in matches:

                sentence = (
                    self._get_text_sentence(
                        text,
                        match.start(),
                        match.end()
                    )
                )

                facts.append({
                    "claim": sentence,
                    "sentence": sentence,
                    "subject": None,
                    "relation": "date",
                    "value": match.group(1),
                    "aliases": [],
                    "entity": match.group(1),
                    "entity_type": fact_type,
                    "fact_type": fact_type
                })

        return facts

    # ==================================================
    # SENTENCE EXTRACTION
    # ==================================================

    def _get_text_sentence(
        self,
        text: str,
        start: int,
        end: int
    ) -> str:

        sentence_start = start

        while sentence_start > 0:

            if text[
                sentence_start - 1
            ] in ".!?":

                break

            sentence_start -= 1

        sentence_end = end

        while sentence_end < len(text):

            if text[
                sentence_end
            ] in ".!?":

                sentence_end += 1
                break

            sentence_end += 1

        return text[
            sentence_start:sentence_end
        ].strip()

    # ==================================================
    # CLEAN TEXT
    # ==================================================

    def _clean_text(
        self,
        text: str
    ) -> str:

        text = re.sub(
            r"```.*?```",
            " ",
            text,
            flags=re.DOTALL
        )

        text = re.sub(
            r"[*_`~]+",
            "",
            text
        )

        text = re.sub(
            r"^\s*#{1,6}\s*",
            "",
            text,
            flags=re.MULTILINE
        )

        text = re.sub(
            r"^\s*[-•]\s*",
            "",
            text,
            flags=re.MULTILINE
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # ==================================================
    # REMOVE DUPLICATES
    # ==================================================

    def _remove_duplicates(
        self,
        facts: List[Dict]
    ) -> List[Dict]:

        seen = set()

        unique_facts = []

        for fact in facts:

            claim = (
                fact.get("claim")
                or ""
            )

            subject = (
                fact.get("subject")
                or ""
            )

            relation = (
                fact.get("relation")
                or ""
            )

            value = (
                fact.get("value")
                or ""
            )

            key = (
                claim.lower().strip(),
                subject.lower().strip(),
                relation.lower().strip(),
                value.lower().strip()
            )

            if key in seen:
                continue

            seen.add(key)

            unique_facts.append(fact)

        return unique_facts


fact_extractor = FactExtractor()