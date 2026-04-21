import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addStudentToClass,
  createEducatorAssignment,
  fetchAssignmentSubmissions,
  fetchWeeklyReport,
  listClassStudents,
  listEducatorAssignments,
  listEducatorClasses,
  removeStudentFromClass,
  sendWeeklyReportEmail,
  weeklyReportPdfUrl,
} from "../api/educatorApi.js";
import AssignmentForm from "../components/educator/AssignmentForm.jsx";
import AssignmentsList from "../components/educator/AssignmentsList.jsx";
import StudentTable from "../components/educator/StudentTable.jsx";

export default function EducatorClassPage() {
  const { id } = useParams();
  const classId = Number(id);
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [report, setReport] = useState(null);
  const [email, setEmail] = useState("");
  const [studentEmail, setStudentEmail] = useState("");
  const [error, setError] = useState("");

  async function loadAll() {
    try {
      const [classRows, studentRows, assignmentRows, reportJson] = await Promise.all([
        listEducatorClasses(),
        listClassStudents(classId),
        listEducatorAssignments(classId),
        fetchWeeklyReport(classId),
      ]);
      setClasses(classRows);
      setStudents(studentRows);
      setAssignments(assignmentRows);
      setReport(reportJson);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => {
    void loadAll();
  }, [classId]);

  const classroom = useMemo(() => classes.find((item) => item.id === classId), [classes, classId]);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-3 text-sm">
        <Link to="/educator" className="text-cyan-700 underline dark:text-cyan-400">
          ← К классам
        </Link>
      </nav>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white">
            {classroom?.name || "Класс"}
          </h1>
          {classroom?.description ? (
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{classroom.description}</p>
          ) : null}
        </div>
        <a
          href={weeklyReportPdfUrl(classId)}
          target="_blank"
          rel="noreferrer"
          className="rounded-xl border border-violet-500/40 px-4 py-2 text-sm font-medium text-violet-800 hover:bg-violet-50 dark:text-violet-300 dark:hover:bg-violet-950/40"
        >
          Скачать PDF-отчёт
        </a>
      </div>
      {error ? <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Ученики</h2>
              <form
                className="flex gap-2"
                onSubmit={async (e) => {
                  e.preventDefault();
                  await addStudentToClass(classId, { email: studentEmail });
                  setStudentEmail("");
                  await loadAll();
                }}
              >
                <input
                  value={studentEmail}
                  onChange={(e) => setStudentEmail(e.target.value)}
                  placeholder="Email ученика"
                  className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950/40"
                />
                <button className="rounded-xl bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500">
                  Добавить
                </button>
              </form>
            </div>
            <div className="mt-4">
              <StudentTable
                items={students}
                classId={classId}
                onRemove={async (_classId, studentId) => {
                  if (!window.confirm("Убрать ученика из класса?")) return;
                  await removeStudentFromClass(classId, studentId);
                  await loadAll();
                }}
              />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Задания</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <AssignmentForm
                classId={classId}
                onCreate={async (payload) => {
                  await createEducatorAssignment(payload);
                  await loadAll();
                }}
              />
              <AssignmentsList
                items={assignments}
                onOpenSubmissions={async (assignment) => {
                  setSubmissions(await fetchAssignmentSubmissions(assignment.id));
                }}
              />
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Сводка недели</h2>
            {report ? (
              <div className="mt-4 space-y-3 text-sm">
                <p>Активных учеников: {report.summary.active_students_last_week}</p>
                <p>Диалогов за неделю: {report.summary.conversations_last_week}</p>
                <p>Всего заданий: {report.summary.assignments_total}</p>
              </div>
            ) : null}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Отправить отчёт</h2>
            <form
              className="mt-4 space-y-3"
              onSubmit={async (e) => {
                e.preventDefault();
                await sendWeeklyReportEmail({ class_id: classId, email });
                alert("Отчёт поставлен в очередь на отправку");
              }}
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="teacher@example.com"
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-950/40"
              />
              <button className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500">
                Отправить на email
              </button>
            </form>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Начатые задания</h2>
            <div className="mt-4 space-y-3 text-sm">
              {submissions.map((row) => (
                <div key={`${row.assignment_id || "s"}-${row.conversation_id}`} className="rounded-xl border border-slate-200 px-4 py-3 dark:border-slate-700">
                  <Link to={`/educator/conversation/${row.conversation_id}`} className="font-medium text-cyan-700 hover:underline dark:text-cyan-400">
                    {row.student_name}
                  </Link>
                  <p className="mt-1 text-slate-500 dark:text-slate-400">{row.title}</p>
                </div>
              ))}
              {submissions.length === 0 ? <p className="text-slate-500 dark:text-slate-500">Выберите задание.</p> : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
