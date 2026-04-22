import { Link } from "react-router-dom";

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <div className="mx-auto max-w-4xl">
        <nav className="mb-6 flex flex-wrap gap-3 text-sm">
          <Link to="/topics" className="text-cyan-700 underline dark:text-cyan-400">
            Темы
          </Link>
          <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
            Чат
          </Link>
        </nav>

        <section className="rounded-[2rem] border border-slate-200 bg-white px-8 py-10 shadow-sm dark:border-slate-800 dark:bg-slate-900/45">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-amber-600 dark:text-amber-300">
            Socrates AI Pro
          </p>
          <h1 className="mt-4 font-display text-4xl font-bold text-slate-950 dark:text-white">
            Расширенная библиотека тем и сценариев
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            В Pro доступны premium-темы, более насыщенные сценарии обсуждений и будущие подборки для отдельных предметов и классов.
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-950/45">
              <p className="font-semibold">Premium-темы</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Этика ИИ, сложная логика, продвинутые социальные и философские кейсы.
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-950/45">
              <p className="font-semibold">Учебные подборки</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Темы под дисциплины и возраст, быстрый старт для урока и домашней практики.
              </p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-950/45">
              <p className="font-semibold">Будущие обновления</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Новые коллекции тем, сценарии для педагогов и персональные рекомендации.
              </p>
            </div>
          </div>

          <div className="mt-8 rounded-3xl border border-amber-300/60 bg-amber-50 px-6 py-5 dark:border-amber-700/40 dark:bg-amber-950/25">
            <p className="text-sm leading-6 text-amber-950 dark:text-amber-100">
              MVP-страница готова для upgrade-flow. Дальше сюда можно подключить оплату и реальные тарифы.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
