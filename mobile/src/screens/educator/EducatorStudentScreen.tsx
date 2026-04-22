import React, { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import { fetchStudentProgress } from "../../api/educator";

export default function EducatorStudentScreen({ route }: any) {
  const studentId = Number(route.params?.id);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetchStudentProgress(studentId).then(setData);
  }, [studentId]);

  if (!data) {
    return (
      <Screen>
        <Text style={styles.title}>Загрузка…</Text>
      </Screen>
    );
  }

  return (
    <Screen>
      <Text style={styles.title}>{route.params?.title || data.student?.email}</Text>
      <View style={styles.grid}>
        <View style={styles.stat}>
          <Text style={styles.label}>Диалоги</Text>
          <Text style={styles.value}>{data.conversations_total}</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.label}>Мудрость</Text>
          <Text style={styles.value}>{data.gamification?.wisdom_points ?? 0}</Text>
        </View>
      </View>
      <Text style={styles.section}>Навыки</Text>
      {data.skills.map((skill: any) => (
        <View key={skill.skill_id} style={styles.skill}>
          <Text style={styles.skillTitle}>{skill.name}</Text>
          <Text style={styles.skillMeta}>{skill.level}/100</Text>
        </View>
      ))}
      <Text style={styles.section}>Частые ошибки</Text>
      {data.frequent_fallacies.map((item: any) => (
        <Text key={item.fallacy_type} style={styles.item}>
          {item.fallacy_type}: {item.count}
        </Text>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 26, fontWeight: "800", marginBottom: 16 },
  grid: { flexDirection: "row", gap: 12, marginBottom: 16 },
  stat: { flex: 1, backgroundColor: "#111827", borderRadius: 18, padding: 16 },
  label: { color: "#94a3b8" },
  value: { color: "#fff", fontSize: 28, fontWeight: "800", marginTop: 8 },
  section: { color: "#fff", fontSize: 18, fontWeight: "700", marginBottom: 10, marginTop: 10 },
  skill: { backgroundColor: "#111827", borderRadius: 14, padding: 14, marginBottom: 8 },
  skillTitle: { color: "#fff" },
  skillMeta: { color: "#94a3b8", marginTop: 4 },
  item: { color: "#cbd5e1", marginBottom: 6 }
});
