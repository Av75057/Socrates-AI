import { api } from "./client";

export async function listClasses() {
  const { data } = await api.get("/educator/classes");
  return data;
}

export async function createClass(body: { name: string; description?: string }) {
  const { data } = await api.post("/educator/classes", body);
  return data;
}

export async function listClassStudents(classId: number) {
  const { data } = await api.get(`/educator/classes/${classId}/students`);
  return data;
}

export async function addStudent(classId: number, email: string) {
  const { data } = await api.post(`/educator/classes/${classId}/students`, { email });
  return data;
}

export async function listAssignments(classId?: number) {
  const { data } = await api.get("/educator/assignments", {
    params: classId ? { class_id: classId } : undefined
  });
  return data;
}

export async function createAssignment(body: Record<string, unknown>) {
  const { data } = await api.post("/educator/assignments", body);
  return data;
}

export async function fetchStudentProgress(studentId: number) {
  const { data } = await api.get(`/educator/students/${studentId}/progress`);
  return data;
}
