import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

function keyFor(sessionId: string) {
  return `mobile_explain_panel_closed_${sessionId}`;
}

export default function ExplainPromptPanel({
  sessionId,
  onExplain
}: {
  sessionId: string;
  onExplain: () => void;
}) {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(keyFor(sessionId)).then((value) => setHidden(value === "true"));
  }, [sessionId]);

  const close = async () => {
    setHidden(true);
    await AsyncStorage.setItem(keyFor(sessionId), "true");
  };

  if (hidden) return null;

  return (
    <View style={styles.card}>
      <Pressable onPress={close} hitSlop={10} style={styles.close}>
        <Text style={styles.closeText}>✕</Text>
      </Pressable>
      <Text style={styles.title}>Окей, давай разберём это вместе 👇</Text>
      <Pressable onPress={onExplain} style={styles.button}>
        <Text style={styles.buttonText}>Показать объяснение</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    position: "relative",
    marginBottom: 10,
    borderRadius: 18,
    padding: 16,
    backgroundColor: "#1d4ed8"
  },
  close: {
    position: "absolute",
    right: 8,
    top: 8,
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center"
  },
  closeText: {
    color: "#dbeafe",
    fontSize: 18
  },
  title: {
    color: "#eff6ff",
    fontSize: 15,
    fontWeight: "600",
    paddingRight: 40
  },
  button: {
    marginTop: 12,
    borderRadius: 14,
    backgroundColor: "#ffffff",
    paddingHorizontal: 14,
    paddingVertical: 12,
    alignSelf: "flex-start"
  },
  buttonText: {
    color: "#1e3a8a",
    fontWeight: "700"
  }
});
