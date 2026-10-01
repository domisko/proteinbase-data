import type { Target } from '../services/api';

interface Props {
  targets: Target[];
  value: string | null;
  onChange: (slug: string) => void;
}

export default function TargetPicker({ targets, value, onChange }: Props) {
  return (
    <label className="field">
      <span className="field-label">Target</span>
      <select value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {targets.map((t) => (
          <option key={t.slug} value={t.slug}>
            {t.name} ({t.designs} designs)
          </option>
        ))}
      </select>
    </label>
  );
}
