import { useState } from "react";

export default function AssignmentForm({ classId, onCreate }) {
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [dueDate, setDueDate] = useState("");

  return (
    <form
      className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900/40"
      onSubmit={(e) => {
        e.preventDefault();
        onCreate?.({
          class_id: classId,
          title,
          prompt,
          due_date: dueDate ? new Date(dueDate).toISOString() : null,
        });
        setTitle("");
        setPrompt("");
        setDueDate("");
      }}
    >
      <h3 className="font-medium text-slate-900 dark:text-slate-100">Новое задание</h3>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Название"
        className="mt-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950/40"
        required
      />
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Тема или стартовый вопрос"
        className="mt-3 min-h-28 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950/40"
        required
      />
      <input
        type="datetime-local"
        value={dueDate}
        onChange={(e) => setDueDate(e.target.value)}
        className="mt-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950/40"
      />
      <button
        type="submit"
        className="mt-3 rounded-xl bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
      >
        Назначить
      </button>
    </form>
  );
}
