import { Link } from "react-router-dom";

export default function LandingFooter() {
  return (
    <footer className="border-t border-slate-800 bg-[#020617] px-6 py-10 text-center text-xs text-slate-600">
      <p>Socrates AI · обучение через диалог</p>
      <p className="mt-2">
        <Link to="/app" className="text-slate-500 hover:text-slate-400">
          Открыть приложение
        </Link>
      </p>
    </footer>
  );
}
