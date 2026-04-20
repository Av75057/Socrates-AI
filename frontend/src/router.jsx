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
import SkillsDashboard from "./pages/SkillsDashboard.jsx";
import PedagogyProfilePage from "./pages/PedagogyProfilePage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import ConversationViewPage from "./pages/ConversationViewPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import ForbiddenPage from "./pages/ForbiddenPage.jsx";
import AdminHomePage from "./pages/AdminHomePage.jsx";
import AdminUsersPage from "./pages/AdminUsersPage.jsx";
import AdminStatsPage from "./pages/AdminStatsPage.jsx";

function RouteErrorScreen() {
  const err = useRouteError();
  const message = err instanceof Error ? err.message : String(err);
  return (
    <div className="min-h-screen bg-red-50 px-6 py-10 text-red-900 dark:bg-[#450a0a] dark:text-red-100">
      <h1 className="font-display text-xl font-bold">Ошибка при отображении страницы</h1>
      <pre className="mt-4 max-w-3xl whitespace-pre-wrap rounded-lg bg-red-100/80 p-4 text-sm text-red-950 dark:bg-black/30 dark:text-red-50/90">
        {message}
      </pre>
      <p className="mt-6 text-sm text-red-700 dark:text-red-200/80">Обновите вкладку или откройте главную.</p>
      <a className="mt-4 inline-block font-medium text-white underline underline-offset-4" href="/">
        На главную
      </a>
    </div>
  );
}

function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-100 px-6 text-center text-slate-800 dark:bg-[#020617] dark:text-slate-200">
      <p className="font-display text-lg font-semibold">Такой страницы нет</p>
      <p className="mt-3 max-w-md text-sm text-slate-600 dark:text-slate-400">
        Админ-панель:{" "}
        <a className="text-amber-700 underline hover:text-amber-600 dark:text-amber-400 dark:hover:text-amber-300" href="/admin">
          /admin
        </a>{" "}
        (нужен вход и роль admin). Чат:{" "}
        <a className="text-cyan-700 underline hover:text-cyan-600 dark:text-cyan-400 dark:hover:text-cyan-300" href="/app">
          /app
        </a>
        .
      </p>
      <a
        className="mt-6 text-emerald-700 underline underline-offset-4 hover:text-emerald-600 dark:text-emerald-400 dark:hover:text-emerald-300"
        href="/"
      >
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
    { path: "/app/admin", element: <Navigate to="/admin" replace /> },
    { path: "/app/admin/*", element: <Navigate to="/admin" replace /> },
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
      path: "/profile/skills",
      element: (
        <PrivateRoute>
          <SkillsDashboard />
        </PrivateRoute>
      ),
    },
    {
      path: "/profile/pedagogy",
      element: (
        <PrivateRoute>
          <PedagogyProfilePage />
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
      path: "/admin",
      element: (
        <AdminRoute>
          <AdminHomePage />
        </AdminRoute>
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
