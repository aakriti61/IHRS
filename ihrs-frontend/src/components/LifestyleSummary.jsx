const TREND_STYLE = {
  rising: { label: "Rising", classes: "bg-amber-50 text-amber-700" },
  falling: { label: "Falling", classes: "bg-sky-50 text-sky-700" },
  stable: { label: "Stable", classes: "bg-teal-light text-teal-dark" },
  insufficient_data: { label: "Need more visits", classes: "bg-surface text-ink/50" },
};

function labelizeTestType(key) {
  return key.charAt(0).toUpperCase() + key.slice(1).replaceAll("_", " ");
}

export default function LifestyleSummary({ data }) {
  const entries = Object.entries(data || {});
  if (entries.length === 0) return null;

  return (
    <section className="mt-8">
      <h2 className="font-display text-lg font-medium text-ink">Lifestyle & trend insights</h2>
      <p className="mt-1 text-xs text-ink/50">
        Based on your lab history over time, compared against your own past results -- not just a single reading.
      </p>
      <div className="mt-3 space-y-3">
        {entries.map(([testType, info]) => {
          const trend = TREND_STYLE[info.trend] || TREND_STYLE.insufficient_data;
          return (
            <div key={testType} className="card">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium text-ink">{labelizeTestType(testType)}</span>
                <span className="text-sm text-ink/70">{info.latest_value} {info.unit}</span>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${trend.classes}`}>
                  {trend.label}
                </span>
              </div>
              {info.recommendation && (
                <p className="mt-2 text-sm text-ink/70">{info.recommendation}</p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}