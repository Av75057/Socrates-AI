import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import PrimaryButton from "../../components/PrimaryButton";
import { addStudent, createAssignment, listAssignments, listClassStudents } from "../../api/educator";

export default function EducatorClassScreen({ navigation, route }: any) {
  const classId = Number(route.params?.id);
  const [students, setStudents] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [email, setEmail] = useState("");
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");

  const load = async () => {
    const [studentRows, assignmentRows] = await Promise.all([
      listClassStudents(classId),
      listAssignments(classId)
    ]);
    setStudents(studentRows);
    setAssignments(assignmentRows);
  };

  useEffect(() => {
    void load();
  }, [classId]);

  return (
    <Screen>
      <Text style={styles.title}>{route.params?.title || "Класс"}</Text>
      <TextField label="Добавить ученика" value={email} onChangeText={setEmail} placeholder="email@example.com" />
      <PrimaryButton
        title="Добавить"
        onPress={async () => {
          await addStudent(classId, email);
          setEmail("");
          await load();
        }}
      />
      <Text style={styles.sectionTitle}>Ученики</Text>
      {students.map((student) => (
        <Pressable
          key={student.id}
          style={styles.card}
          onPress={() => navigation.navigate("EducatorStudent", { id: student.id, title: student.full_name || student.email })}
        >
          <Text style={styles.cardTitle}>{student.full_name || student.email}</Text>
          <Text style={styles.cardMeta}>{student.wisdom_points} wisdom · difficulty {student.current_difficulty}/5</Text>
        </Pressable>
      ))}
      <View style={styles.form}>
        <Text style={styles.sectionTitle}>Новое задание</Text>
        <TextField label="Название" value={title} onChangeText={setTitle} />
        <TextField label="Prompt" value={prompt} onChangeText={setPrompt} multiline />
        <PrimaryButton
          title="Назначить"
          onPress={async () => {
            await createAssignment({ class_id: classId, title, prompt });
            setTitle("");
            setPrompt("");
            await load();
          }}
        />
      </View>
      <Text style={styles.sectionTitle}>Задания</Text>
      {assignments.map((assignment) => (
        <View key={assignment.id} style={styles.card}>
          <Text style={styles.cardTitle}>{assignment.title}</Text>
          <Text style={styles.cardMeta}>{assignment.prompt}</Text>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 26, fontWeight: "800", marginBottom: 16 },
  sectionTitle: { color: "#fff", fontSize: 18, fontWeight: "700", marginTop: 18, marginBottom: 10 },
  card: { backgroundColor: "#111827", borderRadius: 18, padding: 16, marginBottom: 12 },
  cardTitle: { color: "#fff", fontWeight: "700", fontSize: 16 },
  cardMeta: { color: "#94a3b8", marginTop: 6 },
  form: { gap: 12, marginTop: 8 }
});
