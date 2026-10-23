import { useEffect, useState } from 'react';
import { getOpportunitySnapshot, type OpportunitySnapshot } from '../lib/opportunities';

export const DATA_URL = `${import.meta.env.BASE_URL}data/opportunities.json`;

export type SnapshotState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; snapshot: OpportunitySnapshot };

export function useOpportunities(): SnapshotState {
  const [state, setState] = useState<SnapshotState>({ status: 'loading' });

  useEffect(() => {
    let active = true;
    getOpportunitySnapshot(DATA_URL)
      .then((snapshot) => {
        if (active) setState({ status: 'ready', snapshot });
      })
      .catch((error: unknown) => {
        if (!active) return;
        const message = error instanceof Error ? error.message : 'Something went wrong';
        setState({ status: 'error', message });
      });
    return () => {
      active = false;
    };
  }, []);

  return state;
}
