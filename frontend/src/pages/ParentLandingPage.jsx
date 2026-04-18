import ParentHero from "../components/landing/ParentHero.jsx";
import ParentProblem from "../components/landing/ParentProblem.jsx";
import ParentSolution from "../components/landing/ParentSolution.jsx";
import ParentTrust from "../components/landing/ParentTrust.jsx";
import ParentControl from "../components/landing/ParentControl.jsx";
import DemoChat from "../components/landing/DemoChat.jsx";
import LandingCta from "../components/landing/LandingCta.jsx";
import LandingFooter from "../components/landing/LandingFooter.jsx";

export default function ParentLandingPage() {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-100">
      <ParentHero />
      <ParentProblem />
      <ParentSolution />
      <DemoChat />
      <ParentTrust />
      <ParentControl />
      <LandingCta variant="parent" />
      <LandingFooter />
    </div>
  );
}
