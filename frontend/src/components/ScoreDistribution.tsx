import { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api, type Distribution, type ScoreInfo } from '../services/api';
import { formatScoreLabel } from '../format';

interface Props {
  target: string;
  scores: ScoreInfo[];
  score: string | null;
  onScoreChange: (score: string) => void;
}

const fmt = (x: number) =>
  Math.abs(x) >= 100 ? x.toFixed(0) : Number(x.toPrecision(3)).toString();

export default function ScoreDistribution({ target, scores, score, onScoreChange }: Props) {
  const [dist, setDist] = useState<Distribution | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!score) return;
    let cancelled = false;
    setDist(null);
    setError(null);
    api
      .distribution(target, score)
      .then((d) => !cancelled && setDist(d))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [target, score]);

  const data =
    dist && dist.bin_edges.length > 1
      ? dist.binder.counts.map((count, i) => ({
          range: `${fmt(dist.bin_edges[i])} – ${fmt(dist.bin_edges[i + 1])}`,
          label: fmt(dist.bin_edges[i]),
          binder: dist.binder.n ? (count / dist.binder.n) * 100 : 0,
          non_binder: dist.non_binder.n ? (dist.non_binder.counts[i] / dist.non_binder.n) * 100 : 0,
          binderCount: count,
          nonBinderCount: dist.non_binder.counts[i],
        }))
      : [];

  return (
    <div>
      <label className="field">
        <span className="field-label">Score</span>
        <select value={score ?? ''} onChange={(e) => onScoreChange(e.target.value)}>
          {scores.map((s) => (
            <option key={s.name} value={s.name}>
              {formatScoreLabel(s.name)} ({s.designs_with_value} designs)
            </option>
          ))}
        </select>
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!dist && !error && score && <p className="note">Loading…</p>}
      {dist && (
        <>
          <p className="note">
            Binders: {dist.binder.n}
            {dist.binder.n < 20 && ' (small sample)'} · Non-binders: {dist.non_binder.n}
            {dist.non_binder.n < 20 && ' (small sample)'}
          </p>
          {data.length === 0 || dist.binder.n === 0 || dist.non_binder.n === 0 ? (
            <p className="note">
              {data.length === 0
                ? 'No values for this score.'
                : `This target has no ${dist.binder.n === 0 ? 'binders' : 'non-binders'} with this score, so the two groups cannot be compared.`}
            </p>
          ) : null}
          {data.length > 0 && (
            <div className="chart">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" interval="preserveStartEnd" />
                  <YAxis unit="%" width={48} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const p = payload[0].payload as (typeof data)[number];
                      return (
                        <div className="tooltip">
                          <strong>{p.range}</strong>
                          <div>
                            Binders: {p.binder.toFixed(1)}% ({p.binderCount})
                          </div>
                          <div>
                            Non-binders: {p.non_binder.toFixed(1)}% ({p.nonBinderCount})
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Legend formatter={(v) => (v === 'binder' ? 'Binders' : 'Non-binders')} />
                  <Bar dataKey="binder" fill="var(--binder)" />
                  <Bar dataKey="non_binder" fill="var(--non-binder)" />
                </BarChart>
              </ResponsiveContainer>
              <p className="note">Share of each group per score range (hover for counts).</p>
            </div>
          )}
          <p className="note">
            Left out: {dist.missing_count} designs with no value for this score;{' '}
            {dist.conflicting_excluded} designs whose source records several different values;{' '}
            {dist.no_result_excluded} designs with no clear binder result.
          </p>
        </>
      )}
    </div>
  );
}
