import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";

const SCENARIO = [
  {
    user: null,
    ai: "Что происходит с объектом, если на него действует сила, а трение почти нулевое?",
  },
  {
    user: "Он будет ускоряться?",
    ai: "Хороший вопрос. Что говорит твоя интуиция про направление ускорения и силу?",
  },
  {
    user: "Наверное, в ту же сторону, куда толкнули?",
    ai: "Именно. А как бы ты объяснил это другу без формул?",
  },
];

export default function DemoChat() {
  const [step, setStep] = useState(0);
  const [messages, setMessages] = useState([{ role: "assistant", text: SCENARIO[0].ai }]);

  const advance = () => {
    if (step >= SCENARIO.length - 1) return;
    const next = step + 1;
    const row = SCENARIO[next];
    setMessages((prev) => [
      ...prev,
      ...(row.user ? [{ role: "user", text: row.user }] : []),
      { role: "assistant", text: row.ai },
    ]);
    setStep(next);
  };

  const done = step >= SCENARIO.length - 1;

  return (
    <section id="demo" className="scroll-mt-20 border-t border-slate-800/80 bg-[#020617] px-6 py-20 text-white">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-bold md:text-4xl">Интерактив за 20 секунд</h2>
        <p className="mt-3 text-slate-400">Люди кликают, не читают — поэтому сначала демо.</p>
      </div>
      <div className="mx-auto mt-10 max-w-xl overflow-hidden rounded-2xl border border-slate-700/80 bg-[#0f172a] shadow-2xl shadow-black/40">
        <div className="border-b border-slate-800 px-4 py-2 text-left text-xs text-slate-500">
          Демо-диалог · не сохраняется
        </div>
        <div className="max-h-[min(420px,55vh)] space-y-3 overflow-y-auto p-4">
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <motion.div
                key={`${i}-${m.text.slice(0, 12)}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "rounded-br-md bg-blue-600 text-white"
                      : "rounded-bl-md border border-slate-600/50 bg-[#1e293b] text-slate-100"
                  }`}
                >
                  {m.text}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        <div className="border-t border-slate-800 p-4">
          {!done ? (
            <button
              type="button"
              onClick={advance}
              className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
            >
              Показать следующий ход
            </button>
          ) : (
            <div className="space-y-3">
              <p className="text-center text-sm text-slate-400">Так выглядит настоящая сессия — только дольше и глубже.</p>
              <Link
                to="/app"
                className="flex w-full items-center justify-center rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500"
              >
                Открыть полный режим
              </Link>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
