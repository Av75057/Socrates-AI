import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage.jsx";
import StudentLandingPage from "./pages/StudentLandingPage.jsx";
import ParentLandingPage from "./pages/ParentLandingPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";

function NotFound() {
  return <Navigate to="/" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/student" element={<StudentLandingPage />} />
        {/* `/parent` в URL иногда блокируют фильтры/«родительский контроль» — основной путь `/for-parents` */}
        <Route path="/for-parents" element={<ParentLandingPage />} />
        <Route path="/parent" element={<Navigate to="/for-parents" replace />} />
        <Route path="/app" element={<ChatPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
