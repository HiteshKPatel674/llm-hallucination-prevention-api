from typing import List, Dict


class ResponseFormatter:
    """Format response with fact verification information"""
    
    def __init__(self):
        pass
    
    def format_response(
        self,
        original_text: str,
        verified_facts: List[Dict],
        contradictions: List[Dict]
    ) -> Dict:
        """
        Format response with verification information
        Returns structured response data
        """
        
        fact_summary = self._create_fact_summary(
            verified_facts,
            contradictions
        )
        
        return {
            "original": original_text,
            "facts": fact_summary,
            "contradictions": contradictions,
            "has_issues": (
                len(contradictions) > 0
                or any(
                    not fact.get('verified')
                    for fact in verified_facts
                )
            )
        }
    
    def _create_fact_spans(
        self,
        verified_facts: List[Dict],
        contradictions: List[Dict]
    ) -> List[Dict]:
        """
        Create structured fact information
        """
        
        spans = []
        
        contradicted_entities = set()
        
        for contradiction in contradictions:
            if 'current_value' in contradiction:
                contradicted_entities.add(
                    contradiction['current_value'].lower()
                )
        
        for fact in verified_facts:
            entity = fact['entity']
            
            if entity.lower() in contradicted_entities:
                status = "contradicted"
            
            elif (
                fact.get('verified')
                and fact.get('confidence') == 'high'
            ):
                status = "verified"
            
            elif (
                fact.get('verified')
                and fact.get('confidence') == 'medium'
            ):
                status = "uncertain"
            
            else:
                status = "unverified"
            
            spans.append({
                "text": entity,
                "status": status,
                "confidence": fact.get(
                    'confidence',
                    'unknown'
                ),
                "wikipedia_url": fact.get(
                    'wikipedia_url'
                ),
                "note": fact.get(
                    'verification_note',
                    ''
                )
            })
        
        return spans
    
    def _create_html_format(
        self,
        text: str,
        fact_spans: List[Dict]
    ) -> str:
        """
        Return original text.
        Frontend formatting can be handled separately.
        """
        return text
    
    def _create_markdown_format(
        self,
        text: str,
        fact_spans: List[Dict]
    ) -> str:
        """
        Return original text.
        Frontend formatting can be handled separately.
        """
        return text
    
    def _create_fact_summary(
        self,
        verified_facts: List[Dict],
        contradictions: List[Dict]
    ) -> List[Dict]:
        """Create a summary of all facts with their status"""
        
        summary = []
        
        contradicted_entities = set()
        
        for contradiction in contradictions:
            if 'current_value' in contradiction:
                contradicted_entities.add(
                    contradiction['current_value'].lower()
                )
        
        for fact in verified_facts:
            entity = fact['entity']
            
            if entity.lower() in contradicted_entities:
                status = "contradicted"
            
            elif (
                fact.get('verified')
                and fact.get('confidence') == 'high'
            ):
                status = "verified"
            
            elif (
                fact.get('verified')
                and fact.get('confidence') == 'medium'
            ):
                status = "uncertain"
            
            else:
                status = "unverified"
            
            summary.append({
                "entity": entity,
                "type": fact['entity_type'],
                "verified": fact.get(
                    'verified',
                    False
                ),
                "confidence": fact.get(
                    'confidence',
                    'unknown'
                ),
                "status": status,
                "wikipedia_url": fact.get(
                    'wikipedia_url'
                ),
                "note": fact.get(
                    'verification_note',
                    ''
                )
            })
        
        return summary


# Create singleton instance
response_formatter = ResponseFormatter()