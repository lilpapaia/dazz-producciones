/**
 * Placeholder temporal para las páginas externas (FEAT-09 Fase 7).
 * Se reemplaza por las páginas reales en la Fase 7. Permite que las rutas
 * /share/:token/* ya funcionen y compilen sin las páginas finales.
 */
const ExternalPlaceholder = ({ label }) => (
  <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
    <div className="text-center">
      <p className="font-bebas text-4xl tracking-[0.2em] text-amber-500 mb-3">DAZZ</p>
      <p className="text-zinc-300 text-sm">{label}</p>
      <p className="text-zinc-600 text-xs mt-2 font-mono uppercase tracking-wider">TODO · Fase 7</p>
    </div>
  </div>
);

export default ExternalPlaceholder;
