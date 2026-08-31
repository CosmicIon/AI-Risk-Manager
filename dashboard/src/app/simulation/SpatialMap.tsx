'use client';

import { useRef, useEffect, useState, useCallback } from 'react';

const MCC_NAMES: Record<string, string> = {
  '5411': 'Grocery',
  '5732': 'Electronics',
  '5651': 'Apparel',
  '5812': 'Dining',
  '4829': 'Money Transfer',
};

interface CoordPoint {
  x: number;
  y: number;
  customer_id?: string;
  terminal_id?: string;
  mcc?: string;
}

interface Props {
  customerCoords: CoordPoint[];
  terminalCoords: CoordPoint[];
  compromisedTerminals: string[];
  compromisedCustomers: string[];
}

export default function SpatialMap({
  customerCoords,
  terminalCoords,
  compromisedTerminals,
  compromisedCustomers,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const animFrameRef = useRef<number>(0);
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 });

  const compromisedTerminalSet = new Set(compromisedTerminals);
  const compromisedCustomerSet = new Set(compromisedCustomers);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver(entries => {
      const { width } = entries[0].contentRect;
      setDimensions({ width: Math.floor(width), height: Math.floor(width * 0.75) });
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Main rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    const W = dimensions.width;
    const H = dimensions.height;
    const pad = 20;

    const toX = (x: number) => pad + (x / 100) * (W - 2 * pad);
    const toY = (y: number) => pad + (y / 100) * (H - 2 * pad);

    let phase = 0;

    const draw = () => {
      phase += 0.02;

      // Clear
      ctx.fillStyle = '#0a0a12';
      ctx.fillRect(0, 0, W, H);

      // Grid lines
      ctx.strokeStyle = 'rgba(30, 30, 46, 0.5)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i <= 10; i++) {
        const gx = toX(i * 10);
        const gy = toY(i * 10);
        ctx.beginPath();
        ctx.moveTo(gx, pad);
        ctx.lineTo(gx, H - pad);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(pad, gy);
        ctx.lineTo(W - pad, gy);
        ctx.stroke();
      }

      // Customers (blue dots)
      const maxCustomers = Math.min(customerCoords.length, 5000);
      const step = Math.max(1, Math.floor(customerCoords.length / maxCustomers));
      ctx.fillStyle = 'rgba(79, 124, 255, 0.35)';
      for (let i = 0; i < customerCoords.length; i += step) {
        const c = customerCoords[i];
        const isCompromised = c.customer_id && compromisedCustomerSet.has(c.customer_id);
        const cx = toX(c.x);
        const cy = toY(c.y);

        if (isCompromised) {
          // Purple glow for compromised customers
          const pulseR = 4 + Math.sin(phase * 2 + i) * 2;
          ctx.fillStyle = 'rgba(167, 139, 250, 0.6)';
          ctx.beginPath();
          ctx.arc(cx, cy, pulseR, 0, Math.PI * 2);
          ctx.fill();

          // Outer glow ring
          ctx.strokeStyle = `rgba(167, 139, 250, ${0.3 + Math.sin(phase * 3) * 0.2})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(cx, cy, pulseR + 4 + Math.sin(phase) * 3, 0, Math.PI * 2);
          ctx.stroke();
        } else {
          ctx.fillStyle = 'rgba(79, 124, 255, 0.35)';
          ctx.beginPath();
          ctx.arc(cx, cy, 1.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Terminals (cyan diamonds)
      for (let i = 0; i < terminalCoords.length; i++) {
        const t = terminalCoords[i];
        const isCompromised = t.terminal_id && compromisedTerminalSet.has(t.terminal_id);
        const tx = toX(t.x);
        const ty = toY(t.y);

        if (isCompromised) {
          // Red pulsing radar for compromised terminals
          const radarR = 3 + Math.sin(phase * 2.5 + i * 0.5) * 2;

          // Outer radar rings
          for (let r = 0; r < 3; r++) {
            const ringPhase = (phase * 1.5 + r * 0.8) % (Math.PI * 2);
            const ringR = Math.max(0.1, radarR + r * 8 + Math.sin(ringPhase) * 4);
            const ringAlpha = Math.max(0, 0.4 - r * 0.15);
            ctx.strokeStyle = `rgba(248, 113, 113, ${ringAlpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(tx, ty, ringR, 0, Math.PI * 2);
            ctx.stroke();
          }

          // Core dot
          ctx.fillStyle = '#f87171';
          ctx.shadowColor = '#f87171';
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.arc(tx, ty, radarR, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        } else {
          // Normal cyan diamond
          ctx.fillStyle = 'rgba(52, 211, 153, 0.7)';
          ctx.save();
          ctx.translate(tx, ty);
          ctx.rotate(Math.PI / 4);
          ctx.fillRect(-2.5, -2.5, 5, 5);
          ctx.restore();
        }
      }

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [customerCoords, terminalCoords, dimensions, compromisedTerminalSet, compromisedCustomerSet]);

  // Hover tooltip
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const tooltip = tooltipRef.current;
    if (!canvas || !tooltip) return;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const W = dimensions.width;
    const H = dimensions.height;
    const pad = 20;

    // Convert pixel to grid coordinates
    const gx = ((mx - pad) / (W - 2 * pad)) * 100;
    const gy = ((my - pad) / (H - 2 * pad)) * 100;

    // Find nearest terminal within 3 grid units
    let nearest: typeof terminalCoords[0] | null = null;
    let nearestDist = 3.0;

    for (const t of terminalCoords) {
      const dist = Math.sqrt((t.x - gx) ** 2 + (t.y - gy) ** 2);
      if (dist < nearestDist) {
        nearest = t;
        nearestDist = dist;
      }
    }

    if (nearest && nearest.terminal_id) {
      const isComp = compromisedTerminalSet.has(nearest.terminal_id);
      const mccName = nearest.mcc ? (MCC_NAMES[nearest.mcc] || nearest.mcc) : 'Unknown';

      tooltip.innerHTML = `
        <strong>${nearest.terminal_id}</strong><br/>
        MCC: ${mccName} (${nearest.mcc})<br/>
        Position: (${nearest.x.toFixed(1)}, ${nearest.y.toFixed(1)})<br/>
        ${isComp ? '<span style="color: var(--danger); font-weight: 700;">⚠ COMPROMISED</span>' : '<span style="color: var(--success);">✓ Normal</span>'}
      `;
      tooltip.style.left = `${mx + 12}px`;
      tooltip.style.top = `${my - 10}px`;
      tooltip.classList.add('visible');
    } else {
      tooltip.classList.remove('visible');
    }
  }, [terminalCoords, dimensions, compromisedTerminalSet]);

  const handleMouseLeave = useCallback(() => {
    const tooltip = tooltipRef.current;
    if (tooltip) tooltip.classList.remove('visible');
  }, []);

  return (
    <div ref={containerRef} className="sim-spatial-container" id="sim-spatial-map">
      <canvas
        ref={canvasRef}
        className="sim-spatial-canvas"
        style={{ width: dimensions.width, height: dimensions.height }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />
      <div ref={tooltipRef} className="sim-spatial-tooltip" />
      <div className="sim-spatial-legend">
        <div className="sim-legend-item">
          <span className="sim-legend-dot" style={{ background: 'rgba(79, 124, 255, 0.7)' }} />
          Customers
        </div>
        <div className="sim-legend-item">
          <span className="sim-legend-dot" style={{ background: 'rgba(52, 211, 153, 0.8)' }} />
          Terminals
        </div>
        <div className="sim-legend-item">
          <span className="sim-legend-dot" style={{ background: '#f87171' }} />
          Compromised (S2)
        </div>
        <div className="sim-legend-item">
          <span className="sim-legend-dot" style={{ background: '#a78bfa' }} />
          Compromised (S3)
        </div>
      </div>
    </div>
  );
}
