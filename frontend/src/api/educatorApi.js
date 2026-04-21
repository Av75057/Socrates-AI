import { apiFetch } from "./client.js";

async function parseJson(res) {
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204 || res.status === 202) return null;
  return res.json();
}

export async function listEducatorClasses() {
  return parseJson(await apiFetch("/educator/classes"));
}

export async function createEducatorClass(body) {
  return parseJson(
    await apiFetch("/educator/classes", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  );
}

export async function deleteEducatorClass(id) {
  return parseJson(await apiFetch(`/educator/classes/${id}`, { method: "DELETE" }));
}

export async function listClassStudents(classId) {
  return parseJson(await apiFetch(`/educator/classes/${classId}/students`));
}

export async function addStudentToClass(classId, body) {
  return parseJson(
    await apiFetch(`/educator/classes/${classId}/students`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  );
}

export async function removeStudentFromClass(classId, studentId) {
  return parseJson(
    await apiFetch(`/educator/classes/${classId}/students/${studentId}`, { method: "DELETE" }),
  );
}

export async function fetchStudentProgress(studentId) {
  return parseJson(await apiFetch(`/educator/students/${studentId}/progress`));
}

export async function listEducatorAssignments(classId = null) {
  const suffix = classId != null ? `?class_id=${encodeURIComponent(classId)}` : "";
  return parseJson(await apiFetch(`/educator/assignments${suffix}`));
}

export async function createEducatorAssignment(body) {
  return parseJson(
    await apiFetch("/educator/assignments", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  );
}

export async function fetchAssignmentSubmissions(id) {
  return parseJson(await apiFetch(`/educator/assignments/${id}/submissions`));
}

export async function fetchWeeklyReport(classId) {
  return parseJson(await apiFetch(`/educator/reports/weekly?class_id=${encodeURIComponent(classId)}`));
}

export async function sendWeeklyReportEmail(body) {
  return parseJson(
    await apiFetch("/educator/reports/send-email", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  );
}

export async function fetchEducatorConversation(id) {
  return parseJson(await apiFetch(`/educator/conversations/${id}`));
}

export function weeklyReportPdfUrl(classId) {
  return `/api/educator/reports/weekly.pdf?class_id=${encodeURIComponent(classId)}`;
}
