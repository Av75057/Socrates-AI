import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminDeleteUser, adminListUsers, adminUpdateUser } from "../api/adminApi.js";

export default function AdminUsersPage() {
  const [q, setQ] = useState("");
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const data = await adminListUsers(q.trim(), 0, 50);
      setUsers(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-4 text-sm">
        <Link to="/admin" className="text-slate-400 underline">
          Админ — главная
        </Link>
        <Link to="/admin/stats" className="text-cyan-400 underline">
          Статистика
        </Link>
        <Link to="/app" className="text-slate-400 underline">
          Чат
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-white">Пользователи</h1>
      <div className="mt-4 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Поиск email"
          className="rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
        />
        <button
          type="button"
          onClick={load}
          className="rounded-lg bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-600"
        >
          Найти
        </button>
      </div>
      {error ? <p className="mt-4 text-red-400">{error}</p> : null}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-500">
              <th className="py-2 pr-4">ID</th>
              <th className="py-2 pr-4">Email</th>
              <th className="py-2 pr-4">Роль</th>
              <th className="py-2 pr-4">Активен</th>
              <th className="py-2 pr-4">Очки</th>
              <th className="py-2">Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-slate-800">
                <td className="py-2 pr-4">{u.id}</td>
                <td className="py-2 pr-4">{u.email}</td>
                <td className="py-2 pr-4">{u.role}</td>
                <td className="py-2 pr-4">{u.is_active ? "да" : "нет"}</td>
                <td className="py-2 pr-4">{u.wisdom_points}</td>
                <td className="py-2">
                  <button
                    type="button"
                    className="mr-2 text-cyan-400 hover:underline"
                    onClick={async () => {
                      await adminUpdateUser(u.id, { is_active: !u.is_active });
                      load();
                    }}
                  >
                    {u.is_active ? "Блок" : "Разблок"}
                  </button>
                  <button
                    type="button"
                    className="text-red-400 hover:underline"
                    onClick={async () => {
                      if (confirm(`Удалить ${u.email}?`)) {
                        await adminDeleteUser(u.id);
                        load();
                      }
                    }}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
