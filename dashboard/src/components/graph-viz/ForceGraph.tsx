'use client';

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: number;
  type: string;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  value: number;
}

const mockNodes: Node[] = [
  { id: 'Card_1', group: 1, type: 'Card' },
  { id: 'Card_2', group: 1, type: 'Card' },
  { id: 'Device_A', group: 2, type: 'Device' },
  { id: 'Device_B', group: 2, type: 'Device' },
  { id: 'Acc_1', group: 3, type: 'Account' },
  { id: 'Acc_2', group: 3, type: 'Account' },
  { id: 'Acc_3', group: 3, type: 'Account' },
];

const mockLinks: Link[] = [
  { source: 'Card_1', target: 'Device_A', value: 2 },
  { source: 'Card_2', target: 'Device_A', value: 1 },
  { source: 'Card_1', target: 'Acc_1', value: 3 },
  { source: 'Device_B', target: 'Acc_2', value: 1 },
  { source: 'Device_B', target: 'Acc_3', value: 1 },
  { source: 'Acc_1', target: 'Acc_2', value: 2 },
];

const colorScale = d3.scaleOrdinal<string, string>()
  .domain(['Card', 'Device', 'Account'])
  .range(['#3b82f6', '#f59e0b', '#22c55e']);

export default function ForceGraph() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    
    // Clear old svg
    d3.select(containerRef.current).selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight || 400;

    const svg = d3.select(containerRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    const simulation = d3.forceSimulation<Node>(mockNodes)
      .force('link', d3.forceLink<Node, Link>(mockLinks).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g')
      .selectAll('line')
      .data(mockLinks)
      .join('line')
      .attr('stroke', 'var(--border-color)')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.value) * 2);

    const node = svg.append('g')
      .selectAll('circle')
      .data(mockNodes)
      .join('circle')
      .attr('r', 12)
      .attr('fill', d => colorScale(d.type))
      .attr('stroke', 'var(--surface-color)')
      .attr('stroke-width', 2);

    node.append('title')
      .text(d => `${d.id} (${d.type})`);

    const labels = svg.append('g')
      .selectAll('text')
      .data(mockNodes)
      .join('text')
      .attr('dy', 20)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', '10px')
      .text(d => d.id);

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!);

      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);
        
      labels
        .attr('x', d => d.x!)
        .attr('y', d => d.y!);
    });

    return () => {
      simulation.stop();
    };
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '400px' }} />;
}
