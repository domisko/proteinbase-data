/**
 * Small display-only formatting helpers. None of these touch what's stored or served — they only
 * clean up how raw source strings (design method ids, score metric names, target slugs) render in
 * the UI. The raw value is always kept available (e.g. as a title/tooltip) so nothing is hidden.
 */

/**
 * Design method ids often end in one or more random id segments appended by the source pipeline,
 * e.g. "many-steps-pKmAbNsPUw" or "bindcraft2-Gjk2g-qn4C". Every real word in these slugs is
 * lowercase, so a trailing hyphen-separated segment containing an uppercase letter is the random
 * suffix, not part of the name. Strip those segments, but never strip down to nothing.
 */
export function formatMethodName(raw: string): string {
  if (!raw) return raw;
  const parts = raw.split('-');
  while (parts.length > 1 && /[A-Z]/.test(parts[parts.length - 1])) {
    parts.pop();
  }
  return parts.join('-');
}

// Known reference-database suffixes that appear concatenated directly onto the metric name with
// no separator in the source data, e.g. "aligned-lengthafdb50", "evaluecath50", "tm-scorepdb100".
const DB_SUFFIXES = ['afdb50', 'cath50', 'pdb100'];

/**
 * Scores named "<metric><db>" with no separator read as one run-on word. Insert the missing
 * "(db)" grouping. Scores that already use underscores (e.g. "boltz2_complex_iplddt") are left
 * untouched — they read fine as-is.
 */
export function formatScoreLabel(raw: string): string {
  for (const db of DB_SUFFIXES) {
    if (raw.endsWith(db) && raw.length > db.length) {
      return `${raw.slice(0, -db.length)} (${db})`;
    }
  }
  return raw;
}

const RAW_SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/**
 * Most targets only have a slug (e.g. "human-serum-albumin"), not a curated display name — the
 * two main targets (Nipah, EGFR) are the exception and already come from the backend formatted.
 * Turn a raw slug into a sentence-cased label; leave anything that doesn't look like a raw slug
 * (i.e. already has a real display name) alone.
 */
export function formatTargetLabel(name: string): string {
  if (!RAW_SLUG.test(name)) return name;
  const spaced = name.replace(/-/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
