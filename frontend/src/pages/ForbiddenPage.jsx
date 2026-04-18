import { Link } from "react-router-dom";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0f172a] px-6 text-center text-slate-200">
      <p className="text-4xl font-bold text-amber-400">403</p>
      <p className="mt-2 text-lg">Недостаточно прав для этой страницы.</p>
      <Link to="/app" className="mt-8 text-cyan-400 underline">
        В чат
      </Link>
    </div>
  );
}
