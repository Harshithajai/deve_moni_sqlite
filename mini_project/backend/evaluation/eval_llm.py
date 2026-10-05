from typing import Dict, Any, List

class LLMEvaluator:
    @staticmethod
    def evaluate_groundedness(response_text: str, retrieved_contexts: List[str]) -> float:
        """Calculates proportion of generated claims supported by retrieved context."""
        claims = [c.strip() for c in response_text.split('.') if len(c.strip()) > 10]
        if not claims:
            return 1.0
        
        supported = 0
        for claim in claims:
            if any(word in context for context in retrieved_contexts for word in claim.split()[:3]):
                supported += 1
        return supported / len(claims)

    @staticmethod
    def evaluate_extraction(predicted: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """Evaluates Observation Domain, Skill, and Behavior Extraction."""
        domain_acc = 1.0 if predicted.get("domain") == ground_truth.get("domain") else 0.0
        
        pred_skills = set(predicted.get("skills", []))
        gt_skills = set(ground_truth.get("skills", []))
        skill_acc = len(pred_skills.intersection(gt_skills)) / max(len(gt_skills), 1)

        pred_behaviors = set(predicted.get("behaviors", []))
        gt_behaviors = set(ground_truth.get("behaviors", []))
        behavior_acc = len(pred_behaviors.intersection(gt_behaviors)) / max(len(gt_behaviors), 1)

        return {
            "domain_accuracy": domain_acc,
            "skill_extraction_accuracy": skill_acc,
            "behavior_extraction_accuracy": behavior_acc
        }