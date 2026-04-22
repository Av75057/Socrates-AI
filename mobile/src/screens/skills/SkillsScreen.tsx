import React, { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import { fetchGamificationMe } from "../../api/gamification";
import { fetchPedagogy, fetchSkills, fetchStatistics } from "../../api/user";

export default function SkillsScreen() {
  const [skills, setSkills] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [gamification, setGamification] = useState<any>(null);
  const [pedagogy, setPedagogy] = useState<any>(null);

  useEffect(() => {
    Promise.all([fetchSkills(), fetchStatistics(), fetchGamificationMe(), fetchPedagogy()]).then(
      ([skillsData, statsData, gamData, pedData]) => {
        setSkills(skillsData || []);
        setStats(statsData);
        setGamification(gamData);
        setPedagogy(pedData);
      }
    );
  }, []);

  return (
    <Screen>
      <Text style={styles.title}>Навыки и прогресс</Text>
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Диалоги</Text>
          <Text style={styles.statValue}>{stats?.conversations_total ?? 0}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Мудрость</Text>
          <Text style={styles.statValue}>{gamification?.wisdom_points ?? 0}</Text>
        </View>
      </View>
      <View style={styles.block}>
        <Text style={styles.blockTitle}>Текущая сложность</Text>
        <Text style={styles.blockValue}>{pedagogy?.current_difficulty ?? 1}/5</Text>
      </View>
      {skills.map((skill) => (
        <View key={skill.skill_id} style={styles.skillCard}>
          <View style={styles.skillHeader}>
            <Text style={styles.skillTitle}>{skill.name}</Text>
            <Text style={styles.skillMeta}>{skill.level}/100</Text>
          </View>
          <View style={styles.barTrack}>
            <View style={[styles.barFill, { width: `${Math.max(4, skill.level)}%` }]} />
          </View>
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  statsRow: { flexDirection: "row", gap: 12, marginBottom: 16 },
  statCard: { flex: 1, backgroundColor: "#111827", borderRadius: 18, padding: 16 },
  statLabel: { color: "#94a3b8", fontSize: 12, textTransform: "uppercase" },
  statValue: { color: "#fff", fontSize: 26, fontWeight: "800", marginTop: 8 },
  block: { backgroundColor: "#1e293b", borderRadius: 18, padding: 16, marginBottom: 16 },
  blockTitle: { color: "#cbd5e1", fontSize: 14 },
  blockValue: { color: "#fff", fontSize: 24, fontWeight: "800", marginTop: 6 },
  skillCard: { backgroundColor: "#111827", borderRadius: 18, padding: 16, marginBottom: 12 },
  skillHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 10 },
  skillTitle: { color: "#fff", fontSize: 16, fontWeight: "700", flex: 1, marginRight: 12 },
  skillMeta: { color: "#94a3b8" },
  barTrack: { height: 10, backgroundColor: "#334155", borderRadius: 999 },
  barFill: { height: 10, backgroundColor: "#22c55e", borderRadius: 999 }
});
