import re
from typing import Dict, List, Optional, Tuple

import requests
import wikipediaapi


class WikipediaVerifier:

    WIKIDATA_API = "https://www.wikidata.org/w/api.php"

    PROPERTY_MAP = {
        "currency": "P38",
        "capital": "P36",
        "population": "P1082",
        "area": "P2046",
        "official_language": "P37",
        "founder": "P112",
        "headquarters": "P159",
    }

    RELATION_LABELS = {
        "currency": "currency",
        "capital": "capital",
        "population": "population",
        "area": "area",
        "official_language": "official language",
        "founder": "founder",
        "headquarters": "headquarters",
    }

    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent=(
                "HallucinationPrevention/1.0 "
                "(Educational Project)"
            )
        )

        self.http = requests.Session()

        self.http.headers.update({
            "User-Agent": (
                "HallucinationPrevention/1.0 "
                "(Educational Project)"
            )
        })

    def verify_fact(self, fact: Dict) -> Dict:

        subject = fact.get("subject")
        relation = fact.get("relation")
        value = fact.get("value")
        aliases = fact.get("aliases", [])

        if not subject:
            return self._verification_result(
                fact,
                "unverified",
                "low",
                "Could not identify the subject."
            )

        if not relation:
            return self._verification_result(
                fact,
                "unverified",
                "low",
                "Could not identify the relation."
            )

        if not value:
            return self._verification_result(
                fact,
                "unverified",
                "low",
                "Could not identify the claimed value."
            )

        wikidata_result = self._verify_with_wikidata(
            subject,
            relation,
            value,
            aliases
        )

        wikipedia_result = self._verify_with_wikipedia(
            subject,
            relation,
            value,
            aliases
        )

        wikidata_status = wikidata_result.get(
            "status",
            "unverified"
        )

        wikipedia_verified = wikipedia_result.get(
            "verified",
            False
        )

        result = {
            **fact,
            "verified": False,
            "status": "unverified",
            "confidence": "low",
            "evidence": None,
            "verification_note": None,
            "wikipedia_title": wikipedia_result.get(
                "wikipedia_title"
            ),
            "wikipedia_url": wikipedia_result.get(
                "wikipedia_url"
            ),
            "wikidata_id": wikidata_result.get(
                "wikidata_id"
            ),
            "wikidata_url": wikidata_result.get(
                "wikidata_url"
            ),
            "wikidata_label": wikidata_result.get(
                "wikidata_label"
            )
        }

        if wikidata_status == "contradicted":

            result["verified"] = False
            result["status"] = "contradicted"
            result["confidence"] = "high"
            result["evidence"] = wikidata_result.get(
                "evidence"
            )

            result["verification_note"] = (
                "The claim conflicts with "
                "structured Wikidata data."
            )

            return result

        if (
            wikidata_status == "verified"
            and wikipedia_verified
        ):

            result["verified"] = True
            result["status"] = "verified"
            result["confidence"] = "high"

            evidence_parts = []

            if wikidata_result.get("evidence"):
                evidence_parts.append(
                    wikidata_result["evidence"]
                )

            if wikipedia_result.get("evidence"):
                evidence_parts.append(
                    "Wikipedia: "
                    + wikipedia_result["evidence"]
                )

            result["evidence"] = " | ".join(
                evidence_parts
            )

            result["verification_note"] = (
                "The claim is supported by "
                "structured Wikidata data and "
                "relevant Wikipedia evidence."
            )

            return result

        if wikidata_status == "verified":

            result["verified"] = True
            result["status"] = "verified"
            result["confidence"] = "high"

            result["evidence"] = (
                wikidata_result.get("evidence")
            )

            result["verification_note"] = (
                "The claim is directly supported "
                "by structured Wikidata data."
            )

            return result

        if wikipedia_verified:

            result["verified"] = True
            result["status"] = "verified"
            result["confidence"] = "medium"

            result["evidence"] = (
                wikipedia_result.get("evidence")
            )

            result["verification_note"] = (
                "The claim is supported by "
                "relevant Wikipedia textual evidence, "
                "but no matching Wikidata statement "
                "was found."
            )

            return result

        result["verified"] = False
        result["status"] = "unverified"
        result["confidence"] = "low"

        result["verification_note"] = (
            "No sufficient structured or textual "
            "evidence was found for the complete claim."
        )

        return result

    def verify_facts(
        self,
        facts: List[Dict]
    ) -> List[Dict]:

        return [
            self.verify_fact(fact)
            for fact in facts
        ]

    def _verify_with_wikidata(
        self,
        subject: str,
        relation: str,
        value: str,
        aliases: List[str]
    ) -> Dict:

        property_id = self.PROPERTY_MAP.get(
            relation
        )

        if not property_id:
            return {
                "status": "unverified",
                "evidence": None
            }

        try:
            subject_entity = (
                self._search_wikidata_entity(
                    subject,
                    relation
                )
            )

            if not subject_entity:
                return {
                    "status": "unverified",
                    "evidence": None
                }

            qid = subject_entity.get("id")

            if not qid:
                return {
                    "status": "unverified",
                    "evidence": None
                }

            entity = self._get_wikidata_entity(qid)

            if not entity:
                return {
                    "status": "unverified",
                    "evidence": None,
                    "wikidata_id": qid
                }

            claims = entity.get(
                "claims",
                {}
            )

            relation_claims = claims.get(
                property_id,
                []
            )

            if not relation_claims:
                return {
                    "status": "unverified",
                    "evidence": None,
                    "wikidata_id": qid,
                    "wikidata_url": (
                        f"https://www.wikidata.org/wiki/{qid}"
                    ),
                    "wikidata_label": (
                        subject_entity.get(
                            "label",
                            subject
                        )
                    )
                }

            for claim in relation_claims:

                mainsnak = claim.get(
                    "mainsnak",
                    {}
                )

                if mainsnak.get(
                    "snaktype"
                ) != "value":
                    continue

                datavalue = mainsnak.get(
                    "datavalue"
                )

                if not datavalue:
                    continue

                matched, actual_value = (
                    self._match_wikidata_value(
                        datavalue,
                        value,
                        aliases
                    )
                )

                if matched:

                    relation_label = (
                        self.RELATION_LABELS.get(
                            relation,
                            relation
                        )
                    )

                    subject_label = (
                        subject_entity.get(
                            "label",
                            subject
                        )
                    )

                    evidence = (
                        f"Wikidata: "
                        f"{subject_label} "
                        f"→ {relation_label} "
                        f"→ {actual_value}"
                    )

                    return {
                        "status": "verified",
                        "evidence": evidence,
                        "wikidata_id": qid,
                        "wikidata_url": (
                            f"https://www.wikidata.org/wiki/{qid}"
                        ),
                        "wikidata_label": subject_label
                    }

            actual_values = []

            for claim in relation_claims:

                mainsnak = claim.get(
                    "mainsnak",
                    {}
                )

                datavalue = mainsnak.get(
                    "datavalue"
                )

                if not datavalue:
                    continue

                _, actual_value = (
                    self._match_wikidata_value(
                        datavalue,
                        "__NO_MATCH__",
                        []
                    )
                )

                if actual_value:
                    actual_values.append(
                        actual_value
                    )

            relation_label = (
                self.RELATION_LABELS.get(
                    relation,
                    relation
                )
            )

            subject_label = (
                subject_entity.get(
                    "label",
                    subject
                )
            )

            if actual_values:

                evidence = (
                    f"Wikidata: "
                    f"{subject_label} "
                    f"→ {relation_label} "
                    f"→ {', '.join(actual_values)}"
                )

                return {
                    "status": "contradicted",
                    "evidence": evidence,
                    "wikidata_id": qid,
                    "wikidata_url": (
                        f"https://www.wikidata.org/wiki/{qid}"
                    ),
                    "wikidata_label": subject_label
                }

            return {
                "status": "unverified",
                "evidence": None,
                "wikidata_id": qid,
                "wikidata_url": (
                    f"https://www.wikidata.org/wiki/{qid}"
                ),
                "wikidata_label": subject_label
            }

        except Exception:
            return {
                "status": "unverified",
                "evidence": None
            }

        
    def _search_wikidata_entity(
        self,
        name: str,
        relation: Optional[str] = None
    ) -> Optional[Dict]:

        try:
            response = self.http.get(
                self.WIKIDATA_API,
                params={
                    "action": "wbsearchentities",
                    "search": name,
                    "language": "en",
                    "uselang": "en",
                    "type": "item",
                    "limit": 20,
                    "format": "json"
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            results = data.get("search", [])

            if not results:
                return None

            normalized_name = self._normalize_text(name)

            # First preference:
            # exact label match
            for result in results:

                label = result.get("label", "")

                if (
                    self._normalize_text(label)
                    == normalized_name
                ):
                    exact_result = result

                    description = (
                        result.get(
                            "description",
                            ""
                        ).lower()
                    )

                    # For country-related relations,
                    # do not immediately accept a generic
                    # exact match such as "China".
                    if relation in {
                        "capital",
                        "currency",
                        "population",
                        "official_language"
                    }:

                        if (
                            "country" in description
                            or "sovereign state" in description
                        ):
                            return result

                        continue

                    return result

            # Second preference:
            # country / sovereign-state entity
            # even when its label is not exactly the
            # searched text.
            if relation in {
                "capital",
                "currency",
                "population",
                "official_language"
            }:

                for result in results:

                    description = (
                        result.get(
                            "description",
                            ""
                        ).lower()
                    )

                    if (
                        "country" in description
                        or "sovereign state" in description
                    ):
                        return result

            # Third preference:
            # alias match
            for result in results:

                aliases = result.get(
                    "aliases",
                    []
                )

                for alias in aliases:

                    if isinstance(alias, dict):
                        alias_value = alias.get(
                            "value",
                            ""
                        )
                    else:
                        alias_value = str(alias)

                    if (
                        self._normalize_text(
                            alias_value
                        )
                        == normalized_name
                    ):
                        return result

            # Final fallback
            return results[0]

        except Exception:
            return None  

    def _get_wikidata_entity(
        self,
        qid: str
    ) -> Optional[Dict]:

        try:

            response = self.http.get(
                self.WIKIDATA_API,
                params={
                    "action": "wbgetentities",
                    "ids": qid,
                    "props": "labels|aliases|claims|sitelinks",
                    "languages": "en",
                    "format": "json"
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            entities = data.get(
                "entities",
                {}
            )

            return entities.get(qid)

        except Exception:
            return None

    def _match_wikidata_value(
        self,
        datavalue: Dict,
        expected_value: str,
        aliases: List[str]
    ) -> Tuple[bool, Optional[str]]:

        value_type = datavalue.get("type")
        value = datavalue.get("value")

        if value_type == "wikibase-entityid":

            qid = value.get("id")

            if not qid:
                return False, None

            entity = self._get_wikidata_entity(qid)

            if not entity:
                return False, qid

            label_data = (
                entity.get("labels", {})
                .get("en")
            )

            label = (
                label_data.get("value")
                if label_data
                else qid
            )

            candidates = [label]

            entity_aliases = (
                entity.get("aliases", {})
                .get("en", [])
            )

            for alias in entity_aliases:

                alias_value = alias.get("value")

                if alias_value:
                    candidates.append(alias_value)

            expected_values = [
                expected_value
            ]

            expected_values.extend(
                aliases or []
            )

            for candidate in candidates:

                candidate_normalized = (
                    self._normalize_text(candidate)
                )

                for expected in expected_values:

                    expected_normalized = (
                        self._normalize_text(expected)
                    )

                    if (
                        candidate_normalized
                        == expected_normalized
                    ):
                        return True, label

            return False, label

        if value_type == "quantity":

            amount = value.get("amount")

            if not amount:
                return False, None

            amount = amount.lstrip("+")

            return (
                self._values_match(
                    amount,
                    expected_value
                ),
                amount
            )

        if value_type == "string":

            actual = str(value)

            if self._values_match(
                actual,
                expected_value
            ):
                return True, actual

            for alias in aliases or []:

                if self._values_match(
                    actual,
                    alias
                ):
                    return True, actual

            return False, actual

        if value_type == "monolingualtext":

            actual = value.get(
                "text",
                ""
            )

            if self._values_match(
                actual,
                expected_value
            ):
                return True, actual

            for alias in aliases or []:

                if self._values_match(
                    actual,
                    alias
                ):
                    return True, actual

            return False, actual

        if value_type == "time":

            actual = value.get(
                "time",
                ""
            )

            return (
                self._values_match(
                    actual,
                    expected_value
                ),
                actual
            )

        return False, None

    
    def _values_match(
        self,
        actual: str,
        expected: str
    ) -> bool:

        if not actual or not expected:
            return False

        actual_normalized = self._normalize_text(
            actual
        )

        expected_normalized = self._normalize_text(
            expected
        )

        if actual_normalized == expected_normalized:
            return True

        actual_tokens = set(
            actual_normalized.split()
        )

        expected_tokens = set(
            expected_normalized.split()
        )

        if (
            expected_tokens
            and expected_tokens.issubset(actual_tokens)
        ):
            return True

        if (
            actual_tokens
            and actual_tokens.issubset(expected_tokens)
        ):
            return True

        return False

    def _normalize_text(
        self,
        text: str
    ) -> str:

        text = str(text).lower().strip()

        text = re.sub(
            r"[^\w\s₹$€£.-]",
            " ",
            text,
            flags=re.UNICODE
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    def _verify_with_wikipedia(
        self,
        subject: str,
        relation: str,
        value: str,
        aliases: List[str]
    ) -> Dict:

        try:

            page = self.wiki.page(subject)

            if not page.exists():

                search_result = (
                    self._search_wikipedia_page(
                        subject
                    )
                )

                if search_result:
                    page = self.wiki.page(
                        search_result
                    )

            if not page.exists():

                return {
                    "verified": False,
                    "evidence": None,
                    "wikipedia_title": None,
                    "wikipedia_url": None
                }

            sentences = []

            if page.summary:

                sentences.extend(
                    self._split_sentences(
                        page.summary
                    )
                )

            evidence = (
                self._find_structured_evidence(
                    subject,
                    relation,
                    value,
                    sentences,
                    aliases
                )
            )

            if not evidence and page.text:

                evidence = (
                    self._find_structured_evidence(
                        subject,
                        relation,
                        value,
                        self._split_sentences(
                            page.text
                        ),
                        aliases
                    )
                )

            return {
                "verified": bool(evidence),
                "evidence": evidence,
                "wikipedia_title": page.title,
                "wikipedia_url": page.fullurl
            }

        except Exception:

            return {
                "verified": False,
                "evidence": None,
                "wikipedia_title": None,
                "wikipedia_url": None
            }

    def _search_wikipedia_page(
        self,
        subject: str
    ) -> Optional[str]:

        try:

            response = self.http.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": subject,
                    "format": "json",
                    "srlimit": 5
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            results = (
                data.get("query", {})
                .get("search", [])
            )

            if not results:
                return None

            return results[0].get(
                "title"
            )

        except Exception:
            return None

    def _split_sentences(
        self,
        text: str
    ) -> List[str]:

        if not text:
            return []

        return [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+",
                text
            )
            if sentence.strip()
        ]

    def _find_structured_evidence(
        self,
        subject: str,
        relation: str,
        value: str,
        sentences: List[str],
        aliases: Optional[List[str]] = None
    ) -> Optional[str]:

        aliases = aliases or []

        subject_keywords = (
            self._normalize_keywords(
                subject
            )
        )

        value_keywords = (
            self._normalize_keywords(
                value
            )
        )

        relation_keywords = (
            self._get_relation_keywords(
                relation
            )
        )

        alias_keywords = set()

        for alias in aliases:

            alias_keywords.update(
                self._normalize_keywords(
                    alias
                )
            )

        best_sentence = None
        best_score = 0.0

        for sentence in sentences:

            sentence_keywords = (
                self._normalize_keywords(
                    sentence
                )
            )

            subject_match = (
                subject_keywords
                & sentence_keywords
            )

            relation_match = (
                relation_keywords
                & sentence_keywords
            )

            value_match = (
                value_keywords
                & sentence_keywords
            )

            alias_match = (
                alias_keywords
                & sentence_keywords
            )

            if not subject_match:
                continue

            if not relation_match:
                continue

            if not value_match and not alias_match:
                continue

            subject_score = (
                len(subject_match)
                / max(
                    len(subject_keywords),
                    1
                )
            )

            relation_score = (
                len(relation_match)
                / max(
                    len(relation_keywords),
                    1
                )
            )

            value_score = (
                len(value_match)
                / max(
                    len(value_keywords),
                    1
                )
            )

            if alias_match:
                value_score = max(
                    value_score,
                    1.0
                )

            score = (
                subject_score * 0.3
                + relation_score * 0.3
                + value_score * 0.4
            )

            if score > best_score:

                best_score = score
                best_sentence = sentence

        return best_sentence

    def _normalize_keywords(
        self,
        text: str
    ) -> set:

        normalized = self._normalize_text(
            text
        )

        return set(
            normalized.split()
        )

    def _get_relation_keywords(
        self,
        relation: str
    ) -> set:

        keywords = {
            "currency": {
                "currency",
                "currencies"
            },

            "capital": {
                "capital"
            },

            "population": {
                "population",
                "populated",
                "inhabitants"
            },

            "area": {
                "area",
                "square",
                "km"
            },

            "official_language": {
                "official",
                "language",
                "languages"
            },

            "founder": {
                "founder",
                "founded",
                "established"
            },

            "headquarters": {
                "headquarters",
                "headquartered"
            }
        }

        return keywords.get(
            relation,
            {relation}
        )

    def _verification_result(
        self,
        fact: Dict,
        status: str,
        confidence: str,
        note: str
    ) -> Dict:

        return {
            **fact,
            "verified": status == "verified",
            "status": status,
            "confidence": confidence,
            "evidence": None,
            "verification_note": note
        }


wikipedia_verifier = WikipediaVerifier()