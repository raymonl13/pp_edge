import React from 'react';

export default function SparkLine({values = []}) {
  if (!values.length) return <svg width="40" height="16"></svg>;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * 40;
      const y = 16 - ((v - min) / (max - min || 1)) * 16;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg width="40" height="16" className="stroke-current fill-none">
      <polyline points={pts} strokeWidth="1" />
    </svg>
  );
}
