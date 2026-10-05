import React, { useState, useEffect } from "react";
import axios from "axios";

export default function ActivitiesPage({ childId }) {
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const fetchRecommendation = async () => {
    setLoading(true);
    setFeedbackSubmitted(false);
    try {
      const token = localStorage.getItem("access_token");
      const res = await axios.post(
        "http://localhost:8000/api/activities/recommend",
        { child_id: childId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRecommendation(res.data);
    } catch (err) {
      console.error("Error fetching recommendation:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (helpful) => {
    try {
      const token = localStorage.getItem("access_token");
      await axios.post(
        "http://localhost:8000/api/activities/feedback",
        {
          activity_id: recommendation.activity_id || 1,
          helpful: helpful,
          rating: rating,
          comment: comment,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error("Error submitting feedback:", err);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Personalized Activities</h1>

      {/* Medical Disclaimer Banner */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-6 rounded text-amber-800 text-sm">
        <strong>Important Notice:</strong> Recommendations are optional activity suggestions meant for developmental support and engagement. They must NOT be treated as medical diagnosis or treatment.
      </div>

      <button
        onClick={fetchRecommendation}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        disabled={loading}
      >
        {loading ? "Generating Suggestion..." : "Get Recommended Activity"}
      </button>

      {recommendation && (
        <div className="mt-6 bg-white p-6 shadow-md rounded-lg border border-gray-200">
          <div className="flex justify-between items-start">
            <h2 className="text-xl font-semibold text-gray-800">{recommendation.title}</h2>
            <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded font-medium">
              {recommendation.domain}
            </span>
          </div>

          <p className="text-gray-600 mt-2">{recommendation.description}</p>

          <div className="grid grid-cols-2 gap-4 mt-4 text-sm text-gray-700">
            <div><strong>Materials:</strong> {recommendation.materials || "None"}</div>
            <div><strong>Duration:</strong> {recommendation.duration || "Flex"}</div>
          </div>

          <div className="mt-4">
            <h3 className="font-semibold text-gray-800">Steps:</h3>
            <ol className="list-decimal list-inside text-gray-600 mt-1 space-y-1">
              {recommendation.steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>

          {recommendation.observation_targets && (
            <div className="mt-4">
              <h3 className="font-semibold text-gray-800">What to Watch For:</h3>
              <p className="text-gray-600 text-sm">{recommendation.observation_targets}</p>
            </div>
          )}

          {/* Reasoning & Evidence */}
          <div className="mt-6 bg-gray-50 p-4 rounded-md text-xs text-gray-600 border-l-2 border-indigo-400">
            <p><strong>Why suggested:</strong> {recommendation.reasoning}</p>
            {recommendation.evidence_sources && recommendation.evidence_sources.length > 0 && (
              <p className="mt-1">
                <strong>Supporting Evidence:</strong> {recommendation.evidence_sources.join(", ")}
              </p>
            )}
          </div>

          {/* Feedback Section */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Was this recommendation helpful?</h3>
            {feedbackSubmitted ? (
              <p className="text-green-600 text-sm font-medium">Thank you for your feedback!</p>
            ) : (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleFeedback(true)}
                    className="bg-green-100 text-green-700 px-3 py-1 rounded text-sm hover:bg-green-200"
                  >
                    👍 Helpful
                  </button>
                  <button
                    onClick={() => handleFeedback(false)}
                    className="bg-red-100 text-red-700 px-3 py-1 rounded text-sm hover:bg-red-200"
                  >
                    👎 Not helpful
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-500">Rating:</label>
                  <select
                    value={rating}
                    onChange={(e) => setRating(Number(e.target.value))}
                    className="border text-xs rounded p-1"
                  >
                    {[5, 4, 3, 2, 1].map((r) => (
                      <option key={r} value={r}>{r} Stars</option>
                    ))}
                  </select>
                </div>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Optional comments..."
                  className="w-full border rounded p-2 text-xs"
                  rows={2}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}