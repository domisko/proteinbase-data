import { Fragment, useState } from 'react';
import type { HitRate } from '../services/api';
import { formatMethodName } from '../format';

const COLLAPSED_ROWS = 15;

function percent(rate: number | null): string {
  return rate === null ? '–' : `${(rate * 100).toFixed(1)}%`;
}

export default function HitRateTable({ rows }: { rows: HitRate[] }) {
  const [showAll, setShowAll] = useState(false);
  if (rows.length === 0) return <p className="note">No designs for this target.</p>;
  const visible = showAll ? rows : rows.slice(0, COLLAPSED_ROWS);
  const firstSmallIndex = visible.findIndex((r) => r.small_sample);
  return (
    <>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Design method</th>
              <th className="num">Binders</th>
              <th className="num">Tested</th>
              <th className="num">No result</th>
              <th className="rate-col">Hit rate</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((r, i) => (
              <Fragment key={r.method}>
                {i === firstSmallIndex && (
                  <tr className="divider-row" key="divider">
                    <td colSpan={5}>Below: methods with fewer than 20 tested designs</td>
                  </tr>
                )}
                <tr className={r.method === 'unlabelled' ? 'muted-row' : undefined}>
                  <td className="method">
                    <span title={r.method}>{formatMethodName(r.method)}</span>
                    {r.small_sample && (
                      <span className="badge" title="Fewer than 20 designs with a clear result">
                        small sample
                      </span>
                    )}
                  </td>
                  <td className="num">{r.binders}</td>
                  <td className="num">{r.labelled}</td>
                  <td className="num">{r.no_result}</td>
                  <td className="rate-col">
                    <div className="rate">
                      <span className="bar" aria-hidden="true">
                        <span style={{ width: `${(r.hit_rate ?? 0) * 100}%` }} />
                      </span>
                      <span className="rate-text">{percent(r.hit_rate)}</span>
                    </div>
                  </td>
                </tr>
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        Hit rate = binders ÷ tested. “Tested” counts designs with a clear binder or non-binder
        result; “No result” designs are listed but not in the rate. Methods tested on fewer than 20
        designs are marked “small sample” and sorted below the rest, since a high rate on a handful
        of designs is easily noise.
      </p>
      {rows.length > COLLAPSED_ROWS && (
        <button type="button" onClick={() => setShowAll(!showAll)}>
          {showAll ? 'Show fewer methods' : `Show all ${rows.length} methods`}
        </button>
      )}
    </>
  );
}
