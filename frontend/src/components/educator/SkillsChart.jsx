function Bar({ label, value }) {
  const width = `${Math.max(4, Math.min(100, Number(value) || 0))}%`;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="text-slate-700 dark:text-slate-200">{label}</span>
        <span className="tabular-nums text-slate-500 dark:text-slate-400">{value}/100</span>
      </div>
      <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800">
        <div className="h-2 rounded-full bg-cyan-500" style={{ width }} />
      </div>
    </div>
  );
}

export default function SkillsChart({ skills }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
      <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Навыки</h2>
      <div className="mt-4 space-y-4">
        {skills.map((skill) => (
          <Bar key={skill.skill_id} label={skill.name} value={skill.level} />
        ))}
      </div>
    </div>
  );
}
