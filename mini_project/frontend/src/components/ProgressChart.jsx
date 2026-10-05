import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const COLORS = ['#2f6fed', '#5a9cff', '#7cd4d1', '#8bb7ff', '#a7d3ff', '#7ea1ff'];

function ProgressChart({ type = 'line', data = [], xKey = 'date', dataKey = 'count', labelKey = 'domain', title }) {
  if (!data || data.length === 0) {
    return <div className="chart-empty">No chart data available.</div>;
  }

  const renderChart = () => {
    if (type === 'area') {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#2f6fed" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#2f6fed" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#dfeaf7" />
            <XAxis dataKey={xKey} stroke="#5d6d82" />
            <YAxis allowDecimals={false} stroke="#5d6d82" />
            <Tooltip />
            <Area type="linear" dataKey={dataKey} stroke="#2f6fed" fill="url(#areaFill)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    if (type === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#dfeaf7" />
            <XAxis dataKey={xKey} stroke="#5d6d82" />
            <YAxis allowDecimals={false} stroke="#5d6d82" />
            <Tooltip />
            <Bar dataKey={dataKey} radius={[8, 8, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`${entry[xKey]}-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );
    }

    if (type === 'pie') {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={data} dataKey={dataKey} nameKey={labelKey} outerRadius={80} innerRadius={35} paddingAngle={2}>
              {data.map((entry, index) => (
                <Cell key={`${entry[labelKey]}-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#dfeaf7" />
          <XAxis dataKey={xKey} stroke="#5d6d82" />
          <YAxis allowDecimals={false} stroke="#5d6d82" />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke="#2f6fed" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="progress-chart">
      {title ? <h4>{title}</h4> : null}
      {renderChart()}
    </div>
  );
}

export default ProgressChart;
