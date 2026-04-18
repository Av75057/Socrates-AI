import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage.jsx";
import StudentLandingPage from "./pages/StudentLandingPage.jsx";
import ParentLandingPage from "./pages/ParentLandingPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/student" element={<StudentLandingPage />} />
        <Route path="/parent" element={<ParentLandingPage />} />
        <Route path="/app" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}
