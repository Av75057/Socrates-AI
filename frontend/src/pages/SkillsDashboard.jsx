import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getUserSkills, resetProgress } from "../api/userApi.js";

const SKILL_TIPS = {
  avoid_straw_man:
    "Перед критикой перефразируй позицию собеседника так, чтобы он согласился с формулировкой.",
  avoid_ad_hominem: "Отделяй человека от тезиса: оспаривай утверждение, а не личность.",
  use_counterexample: "Добавляй «например…», «представь…» или условные конструкции, чтобы проверить идею.",
  ask_clarifying: "Начинай с уточняющих вопросов или явно спрашивай, что имелось в виду.",
  structure_argument: "Связывай тезис и вывод словами «потому что», «следовательно», «таким образом».",
  logical_consistency: "Проследи, чтобы выводы не противоречили друг другу в рамках одного ответа.",
};

function barColor(level) {
  const t = Math.max(0, Math.min(100, level)) / 100;
  const h = Math.round(120 * t);
  return `hsl(${h}, 65%, 42%)`;
}

function SkillRow({ skill }) {
  const tip = SKILL_TIPS[skill.skill_id] || "Практикуйся в диалогах с тьютором: навык растёт после осмысленных ответов.";
  const lv = Number(skill.level) || 0;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/50">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-base font-semibold text-slate-900 dark:text-white">{skill.name}</h2>
        <span className="tabular-nums text-sm text-slate-500 dark:text-slate-400">{lv}/100</span>
      </div>
      {skill.description ? (
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{skill.description}</p>
      ) : null}
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">Как прокачать: {tip}</p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: barColor(lv) }}
          initial={{ width: 0 }}
          animate={{ width: `${lv}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export default function SkillsDashboard() {
  const [skills, setSkills] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const data = await getUserSkills();
      setSkills(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const sorted = useMemo(() => [...skills].sort((a, b) => (a.skill_id || "").localeCompare(b.skill_id || "")), [skills]);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-8 flex flex-wrap gap-4 text-sm">
        <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
          Чат
        </Link>
        <Link to="/profile" className="text-cyan-700 underline dark:text-cyan-400">
          Профиль
        </Link>
        <Link to="/profile/pedagogy" className="text-cyan-700 underline dark:text-cyan-400">
          Педагогика
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Навыки</h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
        Уровни обновляются после твоих ответов в чате (в фоне). График по дням можно добавить позже; сейчас —
        текущий срез.
      </p>
      {error ? <p className="mt-4 text-red-600 dark:text-red-400">{error}</p> : null}
      {loading ? <p className="mt-6 text-slate-500">Загрузка…</p> : null}
      <div className="mx-auto mt-6 grid max-w-3xl gap-4">
        {sorted.map((s) => (
          <SkillRow key={s.skill_id} skill={s} />
        ))}
      </div>
      <div className="mx-auto mt-10 max-w-3xl rounded-lg border border-dashed border-slate-300 p-4 text-xs text-slate-500 dark:border-slate-600 dark:text-slate-400">
        <p className="font-medium text-slate-700 dark:text-slate-300">Сброс прогресса (тест)</p>
        <button
          type="button"
          className="mt-2 rounded-lg border border-red-300 px-3 py-1.5 text-red-800 hover:bg-red-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950/50"
          onClick={async () => {
            if (!confirm("Обнулить навыки и педагогику в БД?")) return;
            try {
              await resetProgress();
              await load();
            } catch (e) {
              alert(e instanceof Error ? e.message : "Ошибка");
            }
          }}
        >
          Сбросить мой прогресс
        </button>
      </div>
    </div>
  );
}
