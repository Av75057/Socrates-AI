import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Switch, Text, View } from "react-native";
import Screen from "../../components/Screen";
import { fetchSettings, updateSettings } from "../../api/user";
import { useThemeStore } from "../../store/themeStore";

export default function SettingsScreen() {
  const { theme, setTheme } = useThemeStore();
  const [notifications, setNotifications] = useState(true);
  const [mode, setMode] = useState("friendly");

  useEffect(() => {
    fetchSettings().then((data) => {
      setNotifications(Boolean(data.notifications_enabled));
      setMode(data.tutor_mode || "friendly");
      if (data.theme === "dark" || data.theme === "light") setTheme(data.theme);
    });
  }, [setTheme]);

  async function persist(next: Record<string, unknown>) {
    await updateSettings(next);
  }

  return (
    <Screen>
      <Text style={styles.title}>Настройки</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Тёмная тема</Text>
        <Switch
          value={theme === "dark"}
          onValueChange={(value) => {
            const next = value ? "dark" : "light";
            setTheme(next);
            void persist({ theme: next });
          }}
        />
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Уведомления</Text>
        <Switch
          value={notifications}
          onValueChange={(value) => {
            setNotifications(value);
            void persist({ notifications_enabled: value });
          }}
        />
      </View>
      <Text style={styles.section}>Режим тьютора</Text>
      {["friendly", "strict", "provocateur"].map((item) => (
        <Pressable
          key={item}
          style={[styles.option, mode === item && styles.optionActive]}
          onPress={() => {
            setMode(item);
            void persist({ tutor_mode: item });
          }}
        >
          <Text style={styles.optionText}>{item}</Text>
        </Pressable>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  row: {
    backgroundColor: "#111827",
    borderRadius: 18,
    padding: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12
  },
  label: { color: "#fff", fontSize: 16, fontWeight: "600" },
  section: { color: "#cbd5e1", marginTop: 8, marginBottom: 12, fontSize: 16 },
  option: { backgroundColor: "#1e293b", borderRadius: 16, padding: 14, marginBottom: 10 },
  optionActive: { borderWidth: 1, borderColor: "#22d3ee" },
  optionText: { color: "#fff", textTransform: "capitalize" }
});
