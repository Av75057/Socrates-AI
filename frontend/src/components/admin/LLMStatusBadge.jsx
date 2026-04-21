export default function LLMStatusBadge({ status }) {
  if (!status) return null;
  const ok =
    status.effective_provider === "openrouter"
      ? status.openrouter_configured
      : status.ollama_reachable;
  return (
    <span
      className={
        ok
          ? "inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200"
          : "inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-950 dark:bg-amber-950/50 dark:text-amber-100"
      }
      title={ok ? "Провайдер готов к работе" : "Проверьте Ollama или ключ OpenRouter"}
    >
      {status.effective_provider}
      {ok ? " · ок" : " · проверьте"}
    </span>
  );
}
