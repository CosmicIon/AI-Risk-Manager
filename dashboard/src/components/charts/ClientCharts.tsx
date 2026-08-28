'use client';

import dynamic from 'next/dynamic';

export const CostWeightedChart = dynamic(() => import('./CostWeightedChart'), { ssr: false });
export const CaseDistributionChart = dynamic(() => import('./CaseDistributionChart'), { ssr: false });
