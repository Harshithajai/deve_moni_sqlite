import csv
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Resolve path to backend root directory
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Force load environment variables from backend/.env and set working Groq model
load_dotenv(backend_dir / ".env", override=True)
os.environ["GROQ_MODEL"] = "openai/gpt-oss-20b"

from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from app.llm.service import ObservationAnalysisService, _rule_based_fallback


def normalize_label(label: str) -> str:
    """Standardize domain labels (e.g., 'Gross Motor' -> 'gross_motor') to prevent false mismatch errors."""
    if not label:
        return "unknown"
    return label.strip().lower().replace("-", "_").replace(" ", "_")


def main():
    csv_path = backend_dir / "observation_data_expanded.csv"
    if not csv_path.exists():
        print(f"Error: Could not find CSV file at {csv_path}")
        return

    rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))

    # Evaluate on a 150-row subset
    subset = rows[:50]
    svc = ObservationAnalysisService()

    llm_true, llm_pred = [], []
    rb_true, rb_pred = [], []
    fallback_count = 0

    print("Evaluating LLM extraction against Groq API...")
    for idx, r in enumerate(subset, start=1):
        text, true_domain = r["observation_text"], r["domain"]
        extraction, used_fallback, _ = svc.analyze(text)

        if used_fallback:
            fallback_count += 1

        llm_true.append(normalize_label(true_domain))
        llm_pred.append(normalize_label(extraction.domain))

        # Live progress output
        if idx % 10 == 0 or idx == len(subset):
            print(f"Processed {idx}/{len(subset)} items... (Fallbacks so far: {fallback_count})")

        # Minimal delay between requests
        time.sleep(0.05)

    print("\nEvaluating Rule-Based extraction across full dataset...")
    for r in rows:
        text, true_domain = r["observation_text"], r["domain"]
        rb_true.append(normalize_label(true_domain))
        rb_pred.append(normalize_label(_rule_based_fallback(text).domain))

    print("\n--- DIAGNOSTICS ---")
    print(f"Total LLM Sample Size: {len(subset)}")
    print(f"Fallback Count: {fallback_count} / {len(subset)}")
    if fallback_count == len(subset):
        print(
            "⚠️ WARNING: 100% of LLM calls failed! Check GROQ_API_KEY or model access."
        )
    elif fallback_count > 0:
        print(f"⚠️ WARNING: {fallback_count} LLM calls fell back to rule-based.")
    else:
        print("✅ SUCCESS: All LLM calls completed via Groq API without fallback!")

    print("\n--- RESULTS ---")
    for name, y_true, y_pred in [
        ("LLM", llm_true, llm_pred),
        ("Rule-based", rb_true, rb_pred),
    ]:
        acc = accuracy_score(y_true, y_pred)
        p, r_, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="macro", zero_division=0
        )
        print(
            f"{name}: acc={acc:.3f} macro_P={p:.3f} macro_R={r_:.3f} macro_F1={f1:.3f}"
        )


if __name__ == "__main__":
    main()