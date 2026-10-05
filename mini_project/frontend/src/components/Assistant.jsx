import React, { useState, useEffect } from 'react';
import api from '../api';
import { tokenKey } from '../auth';

export default function Assistant() {
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem(tokenKey);
    api
      .get('/api/children', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        setChildren(res.data);
        if (res.data.length > 0) setSelectedChildId(res.data[0].id);
      })
      .catch((err) => {
        setLoadError(
          err.response?.status === 401
            ? 'Your session has expired. Please log in again.'
            : 'Failed to load child profiles. Please try again.'
        );
      });
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!question.trim() || !selectedChildId) return;

    const userMsg = { sender: 'user', text: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const token = localStorage.getItem(tokenKey);
      const res = await api.post(
        '/api/ai/ask',
        {
          child_id: parseInt(selectedChildId),
          question: question,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const aiMsg = { sender: 'ai', data: res.data };
      setMessages((prev) => [...prev, aiMsg]);
      setQuestion('');
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', error: 'Failed to process request. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      <h2>DevCare AI Caregiver Assistant</h2>
      <p style={{ color: '#666', fontSize: '0.9rem' }}>
        Evidence-grounded developmental guidance backed by research papers.
      </p>

      {loadError && (
        <p style={{ color: 'red', fontSize: '0.9rem' }}>{loadError}</p>
      )}

      {/* Child Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label>Select Child Profile: </label>
        <select
          value={selectedChildId}
          onChange={(e) => setSelectedChildId(e.target.value)}
          style={{ padding: '8px', borderRadius: '4px', marginLeft: '10px' }}
        >
          {children.map((child) => (
            <option key={child.id} value={child.id}>
              {child.name}
            </option>
          ))}
        </select>
      </div>

      {/* Chat Container */}
      <div
        style={{
          border: '1px solid #ddd',
          borderRadius: '8px',
          minHeight: '400px',
          padding: '20px',
          backgroundColor: '#fafafa',
          marginBottom: '20px',
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: '20px',
              textAlign: msg.sender === 'user' ? 'right' : 'left',
            }}
          >
            {msg.sender === 'user' ? (
              <div
                style={{
                  display: 'inline-block',
                  background: '#007bff',
                  color: '#fff',
                  padding: '10px 15px',
                  borderRadius: '15px',
                  maxWidth: '70%',
                }}
              >
                {msg.text}
              </div>
            ) : msg.error ? (
              <div style={{ color: 'red' }}>{msg.error}</div>
            ) : (
              <div
                style={{
                  background: '#ffffff',
                  border: '1px solid #e0e0e0',
                  padding: '15px',
                  borderRadius: '8px',
                  textAlign: 'left',
                }}
              >
                <p><strong>Answer:</strong> {msg.data.answer}</p>

                {msg.data.why_this_may_help && (
                  <p><strong>Why This May Help:</strong> {msg.data.why_this_may_help}</p>
                )}

                {msg.data.suggested_activities?.length > 0 && (
                  <div>
                    <strong>Suggested Activities:</strong>
                    <ul>
                      {msg.data.suggested_activities.map((act, i) => (
                        <li key={i}>{act}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {msg.data.how_to_try_at_home?.length > 0 && (
                  <div>
                    <strong>How to Try It at Home:</strong>
                    <ul>
                      {msg.data.how_to_try_at_home.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {msg.data.what_to_observe?.length > 0 && (
                  <div>
                    <strong>What to Observe:</strong>
                    <ul>
                      {msg.data.what_to_observe.map((obs, i) => (
                        <li key={i}>{obs}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Evidence Sources / Citation Cards */}
                {msg.data.evidence_sources?.length > 0 && (
                  <div style={{ marginTop: '15px', background: '#f0f4f8', padding: '10px', borderRadius: '6px' }}>
                    <strong>📚 Evidence Sources:</strong>
                    {msg.data.evidence_sources.map((src, i) => (
                      <div key={i} style={{ fontSize: '0.85rem', marginTop: '8px', borderBottom: '1px #ccc dotted', paddingBottom: '4px' }}>
                        <div><strong>{src.title}</strong> ({src.year || 'N/A'})</div>
                        <div>Authors: {src.authors}</div>
                        {src.doi && <div>DOI: {src.doi}</div>}
                        <div style={{ fontStyle: 'italic', color: '#555' }}>"{src.relevant_passage}"</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Safety Note */}
                <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#888', fontStyle: 'italic' }}>
                  ⚠️ {msg.data.safety_note}
                </div>
              </div>
            )}
          </div>
        ))}
        {loading && <p>Searching evidence base and preparing response...</p>}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a developmental question (e.g., What activities encourage turn-taking?)"
          style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ padding: '10px 20px', background: '#28a745', color: '#fff', border: 'none', borderRadius: '4px' }}
        >
          Ask Assistant
        </button>
      </form>
    </div>
  );
}