import StudentHero from "../components/landing/StudentHero.jsx";
import StudentPain from "../components/landing/StudentPain.jsx";
import DemoChat from "../components/landing/DemoChat.jsx";
import StudentSkillTeaser from "../components/landing/StudentSkillTeaser.jsx";
import StudentExperience from "../components/landing/StudentExperience.jsx";
import LandingCta from "../components/landing/LandingCta.jsx";
import LandingFooter from "../components/landing/LandingFooter.jsx";

export default function StudentLandingPage() {
  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100">
      <StudentHero />
      <StudentPain />
      <DemoChat />
      <StudentSkillTeaser />
      <StudentExperience />
      <LandingCta variant="student" />
      <LandingFooter />
    </div>
  );
}
