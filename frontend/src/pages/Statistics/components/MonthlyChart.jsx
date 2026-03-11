import { memo } from 'react';
import { TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const tooltipStyle = { backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '4px', color: '#f4f4f5' };

const MonthlyChart = memo(({ data, year, geoFilter }) => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6">
    <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
      <TrendingUp size={20} className="text-amber-500" />
      Evolucion Gastos Mensual
    </h3>
    <p className="text-xs text-zinc-600 mb-6">
      Ano completo{geoFilter ? ` \u00B7 ${geoFilter}` : ''}
    </p>

    {data && data.some(m => m.total > 0) ? (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
          <XAxis dataKey="month_name" stroke="#71717a" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
          <YAxis stroke="#71717a" tick={{ fill: '#a1a1aa', fontSize: 12 }}
            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)} />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value) => [`${value.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`, 'Total']}
          />
          <Line type="monotone" dataKey="total" stroke="#f59e0b" strokeWidth={3}
            dot={{ fill: '#f59e0b', r: 4 }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    ) : (
      <div className="h-[300px] flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-500 text-lg mb-2">📊</p>
          <p className="text-zinc-500">No hay datos{geoFilter ? ` (${geoFilter})` : ''} en {year}</p>
        </div>
      </div>
    )}
  </div>
));

MonthlyChart.displayName = 'MonthlyChart';

export default MonthlyChart;
