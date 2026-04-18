import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext.jsx";

export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f172a] text-slate-300">
        Загрузка…
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (String(user.role || "").toLowerCase() !== "admin") {
    return <Navigate to="/forbidden" replace />;
  }
  return children;
}
