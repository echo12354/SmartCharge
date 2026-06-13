export const PILE_LABELS: Record<string, string> = {
  A: '快充1 (A)',
  B: '快充2 (B)',
  C: '慢充1 (C)',
  D: '慢充2 (D)',
  E: '慢充3 (E)',
}

export const PILE_ALIAS: Record<string, string> = {
  A: 'F1',
  B: 'F2',
  C: 'T1',
  D: 'T2',
  E: 'T3',
}

export const STATION_COLUMNS = [
  { pileId: 'A', label: '快充1', alias: 'F1' },
  { pileId: 'B', label: '快充2', alias: 'F2' },
  { pileId: 'C', label: '慢充1', alias: 'T1' },
  { pileId: 'D', label: '慢充2', alias: 'T2' },
  { pileId: 'E', label: '慢充3', alias: 'T3' },
] as const

export const SYSTEM_CONFIG = {
  fastPower: 30,
  slowPower: 10,
  waitingCapacity: 10,
  pileQueueCapacity: 3,
  serviceFee: 0.8,
  peakPrice: 1.0,
  normalPrice: 0.7,
  valleyPrice: 0.4,
}

const FAST_PILES = new Set(['A', 'B'])

export function pileChargeMode(pileId: string): 'fast' | 'slow' | null {
  if (FAST_PILES.has(pileId)) return 'fast'
  if (pileId in PILE_LABELS && !FAST_PILES.has(pileId)) return 'slow'
  return null
}
