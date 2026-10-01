import { useEffect, useState } from 'react';
import Attribution from '../components/Attribution';
import HitRateTable from '../components/HitRateTable';
import ScoreDistribution from '../components/ScoreDistribution';
import TargetPicker from '../components/TargetPicker';
import { api, type HitRate, type ScoreInfo, type Target } from '../services/api';

const PREFERRED_SCORES = ['boltz2_iptm', 'esmfold_plddt'];

export default function Dashboard() {
  const [targets, setTargets] = useState<Target[] | null>(null);
  const [target, setTarget] = useState<string | null>(null);
  const [rates, setRates] = useState<HitRate[] | null>(null);
  const [scores, setScores] = useState<ScoreInfo[]>([]);
  const [score, setScore] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .targets()
      .then((t) => {
        setTargets(t);
        setTarget(t[0]?.slug ?? null);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!target) return;
    let cancelled = false;
    setRates(null);
    setScores([]);
    setScore(null);
    setError(null);
    Promise.all([api.hitRates(target), api.scores(target)])
      .then(([r, s]) => {
        if (cancelled) return;
        setRates(r);
        setScores(s);
        const names = s.map((x) => x.name);
        setScore(PREFERRED_SCORES.find((p) => names.includes(p)) ?? names[0] ?? null);
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [target]);

  return (
    <div className="page">
      <header>
        <h1>Binder hit rate by design method</h1>
        <p className="lede">
          Pick a target to see each design method's binder hit rate and tested count, and which
          computational scores separate binders from non-binders. Methods were tested in very
          different numbers, so a high rate on a handful of designs isn't strong evidence; methods
          with at least 20 tested designs are shown first, with smaller samples below.
        </p>
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!targets && !error && <p className="note">Loading…</p>}

      {targets && targets.length > 0 && (
        <>
          <TargetPicker targets={targets} value={target} onChange={setTarget} />
          <section>
            <h2>Hit rate by design method</h2>
            {rates ? <HitRateTable rows={rates} /> : !error && <p className="note">Loading…</p>}
          </section>
          {target && scores.length > 0 && (
            <section>
              <h2>Scores: binders vs non-binders</h2>
              <ScoreDistribution
                target={target}
                scores={scores}
                score={score}
                onScoreChange={setScore}
              />
            </section>
          )}
        </>
      )}
      <Attribution />
    </div>
  );
}
