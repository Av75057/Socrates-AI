import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity } from "react-native";

const ITEMS = [
  { id: "try", label: "Попробую" },
  { id: "dontknow", label: "Не знаю" },
  { id: "hint", label: "Подсказка" },
  { id: "simpler", label: "Объясни проще" }
];

export default function QuickActions({ onPress }: { onPress: (id: string) => void }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {ITEMS.map((item) => (
        <TouchableOpacity key={item.id} style={styles.pill} onPress={() => onPress(item.id)}>
          <Text style={styles.text}>{item.label}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    gap: 8,
    paddingVertical: 8
  },
  pill: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#334155",
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#111827"
  },
  text: {
    color: "#e2e8f0",
    fontSize: 13,
    fontWeight: "600"
  }
});
