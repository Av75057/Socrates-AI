import { Link } from "react-router-dom";

export default function LandingFooter() {
  return (
    <footer className="border-t border-slate-800 bg-[#020617] px-6 py-10 text-center text-xs text-slate-600">
      <p>Socrates AI · обучение через диалог</p>
      <p className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-2">
        <Link to="/" className="text-slate-500 hover:text-slate-400">
          Кто ты?
        </Link>
        <Link to="/student" className="text-slate-500 hover:text-slate-400">
          Ученикам
        </Link>
        <Link to="/for-parents" className="text-slate-500 hover:text-slate-400">
          Родителям
        </Link>
        <Link to="/app" className="text-slate-500 hover:text-slate-400">
          Приложение
        </Link>
      </p>
    </footer>
  );
}
