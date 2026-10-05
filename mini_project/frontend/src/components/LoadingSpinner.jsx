function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="loading-card">
      <div className="spinner" aria-label="Loading" />
      <span>{message}</span>
    </div>
  );
}

export default LoadingSpinner;
