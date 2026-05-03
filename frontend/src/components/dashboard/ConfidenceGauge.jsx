export default function ConfidenceGauge({ confidence }) {
  const pct = Math.round((confidence || 0) * 100);
  const angle = -90 + (pct / 100) * 180;
  const color = pct > 70 ? '#22c55e' : pct > 40 ? '#f59e0b' : '#ef4444';
  const label = pct > 70 ? 'Strong' : pct > 40 ? 'Medium' : 'Weak';

  const r = 60;
  const cx = 80;
  const cy = 80;

  const startAngle = -180;
  const endAngle = 0;
  const currentAngle = startAngle + (pct / 100) * (endAngle - startAngle);

  const toRad = (deg) => deg * Math.PI / 180;

  const arcPath = (start, end, radius) => {
    const x1 = cx + radius * Math.cos(toRad(start));
    const y1 = cy + radius * Math.sin(toRad(start));
    const x2 = cx + radius * Math.cos(toRad(end));
    const y2 = cy + radius * Math.sin(toRad(end));
    const largeArc = end - start > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  const needleX = cx + (r - 10) * Math.cos(toRad(currentAngle));
  const needleY = cy + (r - 10) * Math.sin(toRad(currentAngle));

  return (
    <div className="confidence-gauge">
      <h4>AI Confidence</h4>
      <svg viewBox="0 0 160 100" className="gauge-svg">
        {/* Background arc */}
        <path d={arcPath(-180, 0, r)} fill="none" stroke="#1a2332" strokeWidth="12" strokeLinecap="round" />

        {/* Red zone */}
        <path d={arcPath(-180, -120, r)} fill="none" stroke="rgba(239,68,68,0.3)" strokeWidth="12" strokeLinecap="round" />
        {/* Yellow zone */}
        <path d={arcPath(-120, -55, r)} fill="none" stroke="rgba(245,158,11,0.3)" strokeWidth="12" strokeLinecap="round" />
        {/* Green zone */}
        <path d={arcPath(-55, 0, r)} fill="none" stroke="rgba(34,197,94,0.3)" strokeWidth="12" strokeLinecap="round" />

        {/* Active arc */}
        <path d={arcPath(-180, currentAngle, r)} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" />

        {/* Needle */}
        <line x1={cx} y1={cy} x2={needleX} y2={needleY} stroke="#fff" strokeWidth="2" />
        <circle cx={cx} cy={cy} r="4" fill="#fff" />

        {/* Labels */}
        <text x={cx} y={cy + 5} textAnchor="middle" fill={color} fontSize="18" fontWeight="bold">
          {pct}%
        </text>
        <text x={cx} y={cy + 18} textAnchor="middle" fill="#9ca3af" fontSize="9">
          {label}
        </text>
      </svg>
    </div>
  );
}
