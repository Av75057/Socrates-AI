import Hero from "../components/landing/Hero.jsx";
import Problem from "../components/landing/Problem.jsx";
import Solution from "../components/landing/Solution.jsx";
import DemoChat from "../components/landing/DemoChat.jsx";
import Benefits from "../components/landing/Benefits.jsx";
import SocialProof from "../components/landing/SocialProof.jsx";
import CTA from "../components/landing/CTA.jsx";
import LandingFooter from "../components/landing/LandingFooter.jsx";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100">
      <Hero />
      <Problem />
      <Solution />
      <DemoChat />
      <Benefits />
      <SocialProof />
      <CTA />
      <LandingFooter />
    </div>
  );
}
