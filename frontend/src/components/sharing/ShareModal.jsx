import { useCallback, useRef, useState } from "react";
import html2canvas from "html2canvas";
import {
  FacebookIcon,
  FacebookShareButton,
  LinkedinIcon,
  LinkedinShareButton,
  TelegramIcon,
  TelegramShareButton,
  TwitterIcon,
  TwitterShareButton,
  WhatsappIcon,
  WhatsappShareButton,
} from "react-share";

const SOCIAL = { className: "flex items-center justify-center rounded-full p-2 transition hover:opacity-90" };

/**
 * @param {{ open: boolean, onClose: () => void, variant: 'achievement' | 'skills' | 'streak', headline: string, subline?: string, wisdomPoints?: number, streakDays?: number }}
 */
export default function ShareModal({ open, onClose, variant, headline, subline, wisdomPoints = 0, streakDays = 0 }) {
  const templateRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState("");

  const siteUrl = typeof window !== "undefined" ? window.location.origin : "";
  const shareUrl = siteUrl || "https://example.com";
  const shareTitle =
    variant === "achievement"
      ? `Я получил достижение «${headline}» в Socrates-AI! А ты?`
      : variant === "streak"
        ? `Серия ${streakDays} дней занятий в Socrates-AI 🔥`
        : "Прокачиваю навыки критического мышления с Socrates-AI";

  const renderCard = useCallback(async () => {
    if (!templateRef.current) return;
    setBusy(true);
    setErr("");
    try {
      const canvas = await html2canvas(templateRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#0f172a",
        logging: false,
      });
      setPreview(canvas.toDataURL("image/png"));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Не удалось собрать изображение");
    } finally {
      setBusy(false);
    }
  }, []);

  const downloadPng = () => {
    if (!preview) return;
    const a = document.createElement("a");
    a.href = preview;
    a.download = "socrates-share.png";
    a.click();
  };

  const tryWebShare = async () => {
    if (!preview || !navigator.share) return;
    try {
      const blob = await (await fetch(preview)).blob();
      const file = new File([blob], "socrates-share.png", { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: shareTitle, text: shareTitle, url: shareUrl });
      } else {
        await navigator.share({ title: shareTitle, text: shareTitle, url: shareUrl });
      }
    } catch {
      /* user cancelled */
    }
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
    } catch {
      /* ignore */
    }
  };

  if (!open) return null;

  const sub =
    subline ||
    (variant === "skills"
      ? "Навыки критического мышления в игровом формате"
      : variant === "streak"
        ? "Регулярность — основа роста"
        : "Учись мыслить глубже");

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm dark:bg-black/70"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-700 dark:bg-[#0f172a]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2">
          <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">Поделиться</h2>
          <button
            type="button"
            className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            onClick={onClose}
          >
            ✕
          </button>
        </div>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Сгенерируй картинку для соцсетей и поделись ссылкой на Socrates-AI.
        </p>

        {/* Вне экрана — html2canvas рендерит этот блок */}
        <div className="pointer-events-none fixed left-[-9999px] top-0">
          <div
            ref={templateRef}
            className="flex h-[315px] w-[600px] flex-col justify-between bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950 p-8 text-white"
            style={{ fontFamily: "system-ui, sans-serif" }}
          >
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-amber-400">Socrates AI</p>
              <p className="mt-4 text-3xl font-bold leading-tight">{headline}</p>
              <p className="mt-3 text-lg text-slate-300">{sub}</p>
            </div>
            <div className="flex items-end justify-between border-t border-white/10 pt-6">
              <div>
                {variant === "skills" || variant === "achievement" ? (
                  <p className="text-3xl font-bold text-amber-300">{wisdomPoints} WP</p>
                ) : (
                  <p className="text-3xl font-bold text-amber-300">{streakDays} дн.</p>
                )}
                <p className="text-sm text-slate-400">
                  {variant === "streak" ? "серия занятий" : "очки мудрости"}
                </p>
              </div>
              <p className="max-w-[200px] text-right text-xs text-slate-500">
                Я прокачиваю критическое мышление с Socrates-AI
              </p>
            </div>
          </div>
        </div>

        {err ? <p className="mt-3 text-sm text-red-600 dark:text-red-400">{err}</p> : null}

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={renderCard}
            className="rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-amber-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {busy ? "Генерация…" : "Собрать превью"}
          </button>
          {preview ? (
            <button
              type="button"
              onClick={downloadPng}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm dark:border-slate-600"
            >
              Сохранить PNG
            </button>
          ) : null}
          {"share" in navigator && preview ? (
            <button
              type="button"
              onClick={tryWebShare}
              className="rounded-full border border-cyan-500/50 px-4 py-2 text-sm text-cyan-800 dark:text-cyan-200"
            >
              Системное меню «Поделиться»
            </button>
          ) : null}
        </div>

        {preview ? (
          <img src={preview} alt="Превью для шеринга" className="mt-4 max-h-56 w-full rounded-lg object-contain" />
        ) : null}

        <div className="mt-6 border-t border-slate-200 pt-4 dark:border-slate-700">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Соцсети</p>
          <div className="flex flex-wrap gap-2">
            <TwitterShareButton url={shareUrl} title={shareTitle} {...SOCIAL}>
              <TwitterIcon size={36} round />
            </TwitterShareButton>
            <FacebookShareButton url={shareUrl} {...SOCIAL}>
              <FacebookIcon size={36} round />
            </FacebookShareButton>
            <TelegramShareButton url={shareUrl} title={shareTitle} {...SOCIAL}>
              <TelegramIcon size={36} round />
            </TelegramShareButton>
            <WhatsappShareButton url={shareUrl} title={shareTitle} separator=" " {...SOCIAL}>
              <WhatsappIcon size={36} round />
            </WhatsappShareButton>
            <LinkedinShareButton url={shareUrl} title={shareTitle} summary={shareTitle} {...SOCIAL}>
              <LinkedinIcon size={36} round />
            </LinkedinShareButton>
          </div>
        </div>

        <button
          type="button"
          onClick={copyLink}
          className="mt-4 w-full rounded-lg border border-slate-200 py-2 text-sm text-slate-700 dark:border-slate-600 dark:text-slate-300"
        >
          Скопировать ссылку на сайт
        </button>
      </div>
    </div>
  );
}
