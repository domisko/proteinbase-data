import { useEffect, useState } from 'react';
import { api, type Meta } from '../services/api';

// Shown in every state, so the credit is fixed text; the snapshot date comes from the API
// and falls back to the known snapshot date if the API is down.
const FALLBACK_DATE = '2026-01-28';

function formatDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}

export default function Attribution() {
  const [meta, setMeta] = useState<Meta | null>(null);
  useEffect(() => {
    api
      .meta()
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);
  return (
    <footer className="attribution">
      Data: Proteinbase, credit to Adaptyv Bio and Proteinbase. Licensed under{' '}
      <a href="https://opendatacommons.org/licenses/by/1-0/">{meta?.licence ?? 'ODC-By'}</a>.
      Snapshot of {formatDate(meta?.snapshot_date ?? FALLBACK_DATE)}.
    </footer>
  );
}
