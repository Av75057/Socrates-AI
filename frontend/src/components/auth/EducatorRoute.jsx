import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";

export default function EducatorRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600 dark:bg-[#0f172a] dark:text-slate-300">
        Загрузка…
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  const role = String(user.role || "").toLowerCase();
  if (role !== "educator" && role !== "admin") {
    return <Navigate to="/forbidden" replace />;
  }
  return children;
}
