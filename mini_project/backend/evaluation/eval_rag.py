import os
import json
import numpy as np
from typing import List, Dict, Any

class RAGEvaluator:
    def __init__(self, vector_store, retriever):
        self.vector_store = vector_store
        self.retriever = retriever

    def precision_at_k(self, retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
        top_k = retrieved_ids[:k]
        relevant_retrieved = set(top_k).intersection(set(ground_truth_ids))
        return len(relevant_retrieved) / k

    def recall_at_k(self, retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
        top_k = retrieved_ids[:k]
        relevant_retrieved = set(top_k).intersection(set(ground_truth_ids))
        if not ground_truth_ids:
            return 0.0
        return len(relevant_retrieved) / len(ground_truth_ids)

    def evaluate_dataset(self, test_dataset: List[Dict[str, Any]], k: int = 3) -> Dict[str, float]:
        precision_scores = []
        recall_scores = []

        for item in test_dataset:
            query = item["query"]
            ground_truth = item["ground_truth_doc_ids"]
            
            # Perform retrieval
            results = self.retriever.retrieve(query, top_k=k)
            retrieved_ids = [doc.metadata.get("doc_id") for doc in results]

            p_k = self.precision_at_k(retrieved_ids, ground_truth, k)
            r_k = self.recall_at_k(retrieved_ids, ground_truth, k)

            precision_scores.append(p_k)
            recall_scores.append(r_k)

        return {
            f"Mean_Precision@{k}": float(np.mean(precision_scores)),
            f"Mean_Recall@{k}": float(np.mean(recall_scores)),
            "Total_Queries": len(test_dataset)
        }

if __name__ == "__main__":
    print("RAG Evaluation Module Ready.")