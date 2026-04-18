import { createBrowserRouter, Navigate, useRouteError } from "react-router-dom";
import AdminRoute from "./components/auth/AdminRoute.jsx";
import PrivateRoute from "./components/auth/PrivateRoute.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import StudentLandingPage from "./pages/StudentLandingPage.jsx";
import ParentLandingPage from "./pages/ParentLandingPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import ConversationViewPage from "./pages/ConversationViewPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import ForbiddenPage from "./pages/ForbiddenPage.jsx";
import AdminUsersPage from "./pages/AdminUsersPage.jsx";
import AdminStatsPage from "./pages/AdminStatsPage.jsx";

function RouteErrorScreen() {
  const err = useRouteError();
  const message = err instanceof Error ? err.message : String(err);
  return (
    <div className="min-h-screen bg-[#450a0a] px-6 py-10 text-red-100">
      <h1 className="font-display text-xl font-bold">Ошибка при отображении страницы</h1>
      <pre className="mt-4 max-w-3xl whitespace-pre-wrap rounded-lg bg-black/30 p-4 text-sm text-red-50/90">{message}</pre>
      <p className="mt-6 text-sm text-red-200/80">Обновите вкладку или откройте главную.</p>
      <a className="mt-4 inline-block font-medium text-white underline underline-offset-4" href="/">
        На главную
      </a>
    </div>
  );
}

function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#020617] px-6 text-center text-slate-200">
      <p className="font-display text-lg font-semibold">Такой страницы нет</p>
      <a className="mt-6 text-emerald-400 underline underline-offset-4 hover:text-emerald-300" href="/">
        Кто ты? — выбор ученик / родитель
      </a>
    </div>
  );
}

const viteBase = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "");
const routerOptions = viteBase ? { basename: viteBase } : {};

export const router = createBrowserRouter(
  [
    { path: "/", element: <LandingPage /> },
    { path: "/student", element: <StudentLandingPage />, errorElement: <RouteErrorScreen /> },
    {
      path: "/for-parents",
      element: <ParentLandingPage />,
      errorElement: <RouteErrorScreen />,
    },
    { path: "/parent", element: <Navigate to="/for-parents" replace /> },
    { path: "/app", element: <ChatPage />, errorElement: <RouteErrorScreen /> },
    { path: "/login", element: <LoginPage /> },
    { path: "/register", element: <RegisterPage /> },
    { path: "/forbidden", element: <ForbiddenPage /> },
    {
      path: "/profile",
      element: (
        <PrivateRoute>
          <ProfilePage />
        </PrivateRoute>
      ),
    },
    {
      path: "/profile/history",
      element: (
        <PrivateRoute>
          <HistoryPage />
        </PrivateRoute>
      ),
    },
    {
      path: "/profile/history/:id",
      element: (
        <PrivateRoute>
          <ConversationViewPage />
        </PrivateRoute>
      ),
    },
    {
      path: "/profile/settings",
      element: (
        <PrivateRoute>
          <SettingsPage />
        </PrivateRoute>
      ),
    },
    {
      path: "/admin/users",
      element: (
        <AdminRoute>
          <AdminUsersPage />
        </AdminRoute>
      ),
    },
    {
      path: "/admin/stats",
      element: (
        <AdminRoute>
          <AdminStatsPage />
        </AdminRoute>
      ),
    },
    { path: "*", element: <NotFoundPage /> },
  ],
  routerOptions,
);
