from typing import List, Dict, Optional
import re


class ContradictionDetector:
    """Detect contradictions in conversation history"""
    
    def __init__(self):
        # Store facts by session
        self.session_facts = {}  # {session_id: [facts]}
        
    def add_facts(self, session_id: str, facts: List[Dict]):
        """Add new facts to session history"""
        if session_id not in self.session_facts:
            self.session_facts[session_id] = []
        
        self.session_facts[session_id].extend(facts)
    
    def detect_contradictions(
        self,
        session_id: str,
        new_facts: List[Dict]
    ) -> List[Dict]:
        """
        Check if new facts contradict previous facts in the conversation
        Returns list of contradictions found
        """
        if session_id not in self.session_facts:
            return []
        
        previous_facts = self.session_facts[session_id]
        contradictions = []
        
        for new_fact in new_facts:
            # Check against all previous facts
            for old_fact in previous_facts:
                contradiction = self._check_fact_pair(
                    new_fact,
                    old_fact
                )
                
                if contradiction:
                    contradictions.append(contradiction)
        
        return contradictions
    
    def _check_fact_pair(
        self,
        fact1: Dict,
        fact2: Dict
    ) -> Optional[Dict]:
        """
        Check if two facts contradict each other
        Returns contradiction details if found, None otherwise
        """
        # Must be about same entity type
        if fact1['entity_type'] != fact2['entity_type']:
            return None
        
        entity_type = fact1['entity_type']
        
        # Check for numeric contradictions
        if entity_type in [
            'CARDINAL',
            'QUANTITY',
            'MONEY',
            'MEASUREMENT',
            'POPULATION'
        ]:
            return self._check_numeric_contradiction(
                fact1,
                fact2
            )
        
        # Check for date contradictions
        if entity_type == 'DATE':
            return self._check_date_contradiction(
                fact1,
                fact2
            )
        
        # Check for entity contradictions
        if entity_type in [
            'GPE',
            'LOC',
            'PERSON',
            'ORG'
        ]:
            return self._check_entity_contradiction(
                fact1,
                fact2
            )
        
        return None
    
    def _check_numeric_contradiction(
        self,
        fact1: Dict,
        fact2: Dict
    ) -> Optional[Dict]:
        """Check if numeric facts contradict"""
        
        num1 = self._extract_number(fact1['entity'])
        num2 = self._extract_number(fact2['entity'])
        
        if num1 is None or num2 is None:
            return None
        
        # Check if they're talking about the same thing
        if not self._same_subject(
            fact1['sentence'],
            fact2['sentence']
        ):
            return None
        
        # Check if numbers differ significantly
        diff_percent = abs(num1 - num2) / max(num1, num2) * 100
        
        if diff_percent > 20:
            return {
                "type": "numeric_contradiction",
                "severity": "high" if diff_percent > 50 else "medium",
                "previous_claim": fact2['sentence'],
                "current_claim": fact1['sentence'],
                "previous_value": fact2['entity'],
                "current_value": fact1['entity'],
                "difference": f"{diff_percent:.1f}% difference",
                "message": (
                    "Contradiction detected: "
                    "Different values for the same claim"
                )
            }
        
        return None
    
    def _check_date_contradiction(
        self,
        fact1: Dict,
        fact2: Dict
    ) -> Optional[Dict]:
        """Check if dates contradict"""
        
        year1 = self._extract_year(fact1['entity'])
        year2 = self._extract_year(fact2['entity'])
        
        if year1 is None or year2 is None or year1 == year2:
            return None
        
        # Check if talking about same subject
        if not self._same_subject(
            fact1['sentence'],
            fact2['sentence']
        ):
            return None
        
        return {
            "type": "date_contradiction",
            "severity": "high",
            "previous_claim": fact2['sentence'],
            "current_claim": fact1['sentence'],
            "previous_value": fact2['entity'],
            "current_value": fact1['entity'],
            "difference": f"{abs(year1 - year2)} years apart",
            "message": (
                "Contradiction: Different dates "
                "for the same event"
            )
        }
    
    def _check_entity_contradiction(
        self,
        fact1: Dict,
        fact2: Dict
    ) -> Optional[Dict]:
        """Check if entity facts contradict"""
        
        pattern1 = self._extract_is_statement(
            fact1['sentence']
        )
        
        pattern2 = self._extract_is_statement(
            fact2['sentence']
        )
        
        if pattern1 and pattern2:
            subject1, claim1 = pattern1
            subject2, claim2 = pattern2
            
            if (
                self._similar_text(subject1, subject2)
                and not self._similar_text(claim1, claim2)
            ):
                return {
                    "type": "entity_contradiction",
                    "severity": "high",
                    "previous_claim": fact2['sentence'],
                    "current_claim": fact1['sentence'],
                    "message": (
                        f"Contradiction: Different information "
                        f"about {subject1}"
                    )
                }
        
        return None
    
    def _extract_number(
        self,
        text: str
    ) -> Optional[float]:
        """Extract numeric value from text"""
        
        text_clean = text.replace(',', '')
        
        multiplier = 1
        
        if 'billion' in text.lower():
            multiplier = 1_000_000_000
        elif 'million' in text.lower():
            multiplier = 1_000_000
        elif 'thousand' in text.lower():
            multiplier = 1_000
        
        match = re.search(
            r'([\d.]+)',
            text_clean
        )
        
        if match:
            try:
                return float(match.group(1)) * multiplier
            except:
                return None
        
        return None
    
    def _extract_year(
        self,
        text: str
    ) -> Optional[int]:
        """Extract year from text"""
        
        match = re.search(
            r'(\d{4})',
            text
        )
        
        if match:
            try:
                return int(match.group(1))
            except:
                return None
        
        return None
    
    def _same_subject(
        self,
        sentence1: str,
        sentence2: str
    ) -> bool:
        """Check if two sentences are about the same subject"""
        
        words1 = sentence1.lower().split()[:5]
        words2 = sentence2.lower().split()[:5]
        
        common = set(words1) & set(words2)
        
        return len(common) >= 2
    
    def _extract_is_statement(
        self,
        sentence: str
    ) -> Optional[tuple]:
        """Extract 'X is Y' patterns from sentence"""
        
        match = re.search(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(.+)',
            sentence
        )
        
        if match:
            return (
                match.group(1),
                match.group(2)
            )
        
        return None
    
    def _similar_text(
        self,
        text1: str,
        text2: str
    ) -> bool:
        """Check if two texts are similar"""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2) / min(
            len(words1),
            len(words2)
        )
        
        return overlap > 0.5
    
    def get_session_summary(
        self,
        session_id: str
    ) -> Dict:
        """Get summary of facts tracked in a session"""
        
        if session_id not in self.session_facts:
            return {
                "total_facts": 0,
                "facts": []
            }
        
        facts = self.session_facts[session_id]
        
        return {
            "total_facts": len(facts),
            "facts": facts
        }
    
    def clear_session(
        self,
        session_id: str
    ):
        """Clear facts for a session"""
        
        if session_id in self.session_facts:
            del self.session_facts[session_id]


# Create singleton instance
contradiction_detector = ContradictionDetector()