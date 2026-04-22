import React, { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export default function ChatComposer({
  onSend,
  loading
}: {
  onSend: (text: string) => void;
  loading?: boolean;
}) {
  const [value, setValue] = useState("");

  return (
    <View style={styles.wrap}>
      <TextInput
        multiline
        value={value}
        onChangeText={setValue}
        placeholder="Напиши, что думаешь…"
        placeholderTextColor="#94a3b8"
        style={styles.input}
      />
      <Pressable
        onPress={() => {
          const text = value.trim();
          if (!text || loading) return;
          setValue("");
          onSend(text);
        }}
        style={styles.send}
      >
        <Ionicons name="send" size={18} color="#fff" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingTop: 8
  },
  input: {
    flex: 1,
    minHeight: 48,
    maxHeight: 120,
    backgroundColor: "#111827",
    borderRadius: 16,
    color: "#f8fafc",
    paddingHorizontal: 14,
    paddingVertical: 12
  },
  send: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: "#06b6d4",
    alignItems: "center",
    justifyContent: "center"
  }
});
