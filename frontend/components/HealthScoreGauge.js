'use client'
import { gradeColor } from '../lib/api'

export default function HealthScoreGauge({ score }) {
  const { total, grade, nutriscore_score, nova_score, additives_score, nutrient_score, summary } = score
  const pct = Math.min(100, Math.max(0, total))
  const color = gradeColor(grade)

  // SVG circle gauge
  const r = 54
  const circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Gauge */}
      <div className="relative w-48 h-48">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          {/* Background ring */}
          <circle cx="60" cy="60" r={r} fill="none" stroke="#2a2a3d" strokeWidth="8" />
          {/* Score ring */}
          <circle
            cx="60" cy="60" r={r}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            style={{ transition: 'stroke-dasharray 1.2s ease', filter: `drop-shadow(0 0 8px ${color})` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display font-800 text-4xl" style={{ color }}>{Math.round(total)}</span>
          <span className="font-display font-700 text-xl" style={{ color }}>{grade}</span>
        </div>
      </div>

      {/* Summary */}
      <p className="text-center text-sm text-muted max-w-xs leading-relaxed">{summary}</p>

      {/* Breakdown bars */}
      <div className="w-full space-y-3">
        {[
          { label: 'Nutriscore', value: nutriscore_score, max: 40 },
          { label: 'NOVA Group', value: nova_score, max: 25 },
          { label: 'Additives', value: additives_score, max: 20 },
          { label: 'Nutrients', value: nutrient_score, max: 15 },
        ].map(({ label, value, max }) => {
          const pct = (value / max) * 100
          const barColor = pct >= 70 ? '#00ff88' : pct >= 40 ? '#ffaa00' : '#ff3366'
          return (
            <div key={label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted font-body">{label}</span>
                <span className="font-mono" style={{ color: barColor }}>{value}/{max}</span>
              </div>
              <div className="h-1.5 rounded-full bg-border overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{ width: `${pct}%`, background: barColor, boxShadow: `0 0 6px ${barColor}` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}