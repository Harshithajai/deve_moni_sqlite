import json
import statistics as st
import sys
import time
from pathlib import Path

# Resolve backend root path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.retriever import retrieve


def main():
    testset_path = backend_dir / "evaluation" / "rag_testset.json"
    if not testset_path.exists():
        print(f"Error: Could not find test set at {testset_path}")
        return

    testset = json.load(open(testset_path, encoding="utf-8"))
    k = 4
    hits, precisions, rr, latencies = [], [], [], []

    print(f"Evaluating RAG retrieval on {len(testset)} test queries...")

    for item in testset:
        t0 = time.time()
        results = retrieve(item["query"], top_k=k)
        latencies.append(time.time() - t0)

        titles = [r.get("title", "") for r in results]
        gt = set(item["ground_truth_titles"])

        hit = any(t in gt for t in titles)
        hits.append(hit)
        precisions.append(len([t for t in titles if t in gt]) / k)

        rank = next(
            (i + 1 for i, t in enumerate(titles) if t in gt), None
        )
        rr.append(1 / rank if rank else 0)

    print("\n--- RAG RETRIEVAL RESULTS ---")
    print(f"Hit Rate@{k}: {sum(hits) / len(hits) * 100:.1f}%")
    print(f"Precision@{k}: {sum(precisions) / len(precisions):.3f}")
    print(f"MRR: {sum(rr) / len(rr):.3f}")
    print(
        f"Latency Median / P95: {st.median(latencies):.3f}s / {sorted(latencies)[int(len(latencies) * 0.95)]:.3f}s"
    )


if __name__ == "__main__":
    main()