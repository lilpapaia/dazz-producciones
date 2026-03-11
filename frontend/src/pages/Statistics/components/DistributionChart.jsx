import { memo, useMemo } from 'react';
import { Globe } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];
const tooltipStyle = { backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '4px', color: '#f4f4f5' };

const DistributionChart = memo(({ data, quarter, year }) => {
  const legendFormatter = useMemo(() => (value, entry) => (
    <span style={{ color: '#a1a1aa', fontSize: '12px' }}>
      {entry.payload.label} ({entry.payload.percentage}%)
    </span>
  ), []);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
      <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
        <Globe size={20} className="text-amber-500" />
        Distribucion por Origen
      </h3>
      <p className="text-xs text-zinc-600 mb-6">
        {quarter ? `Q${quarter}` : 'Ano completo'}
      </p>

      {data && data.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="45%"
              labelLine={false}
              outerRadius={75}
              fill="#8884d8"
              dataKey="total"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`, 'Total']}
            />
            <Legend formatter={legendFormatter} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-[300px] flex items-center justify-center">
          <div className="text-center">
            <p className="text-zinc-500 text-lg mb-2">🌍</p>
            <p className="text-zinc-500">No hay gastos registrados{quarter ? ` en Q${quarter}` : ''} de {year}</p>
          </div>
        </div>
      )}
    </div>
  );
});

DistributionChart.displayName = 'DistributionChart';

export default DistributionChart;
