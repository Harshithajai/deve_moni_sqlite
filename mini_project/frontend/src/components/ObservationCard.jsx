function ObservationCard({ observation }) {
  const displayDate = observation.date || new Date(observation.observation_date).toLocaleDateString();

  return (
    <article className="observation-card">
      <div className="observation-card-header">
        <span className="observation-pill">{observation.domain}</span>
        <span className="observation-date">{displayDate}</span>
      </div>
      <h4>{observation.skill}</h4>
      <p>{observation.observation_text}</p>
      <div className="observation-meta">
        <span>Confidence: {observation.confidence_score}%</span>
      </div>
    </article>
  );
}

export default ObservationCard;
