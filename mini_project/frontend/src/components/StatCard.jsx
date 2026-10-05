const toneClasses = {
  default: 'stat-card',
  success: 'stat-card stat-card-success',
  primary: 'stat-card stat-card-primary',
};

function StatCard({ title, value, subtitle, tone = 'default' }) {
  return (
    <div className={toneClasses[tone] || toneClasses.default}>
      <span className="stat-label">{title}</span>
      <strong>{value}</strong>
      {subtitle ? <small>{subtitle}</small> : null}
    </div>
  );
}

export default StatCard;
