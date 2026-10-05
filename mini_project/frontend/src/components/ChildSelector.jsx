function ChildSelector({ children, value, onChange, label = 'Child selector' }) {
  return (
    <label className="field-block">
      <span>{label}</span>
      <select value={value} onChange={onChange}>
        <option value="">Select a child</option>
        {children.map((child) => (
          <option key={child.id} value={child.id}>{child.name}</option>
        ))}
      </select>
    </label>
  );
}

export default ChildSelector;
