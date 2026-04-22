import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import { apiErrorMessage } from "../../api/client";
import { fetchPublicShare } from "../../api/share";

export default function PublicShareScreen({ route }: any) {
  const [slug, setSlug] = useState(route?.params?.slug || "");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadShare(nextSlug: string) {
    const normalized = nextSlug.trim();
    if (!normalized) {
      setError("Введите slug публичного диалога.");
      setData(null);
      return;
    }
    try {
      setLoading(true);
      setError("");
      setData(await fetchPublicShare(normalized));
    } catch (e) {
      setError(apiErrorMessage(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const incoming = route?.params?.slug;
    if (incoming) {
      setSlug(incoming);
      void loadShare(incoming);
    }
  }, [route?.params?.slug]);

  return (
    <Screen>
      <Text style={styles.title}>Публичный диалог</Text>
      <Text style={styles.subtitle}>Откройте диалог по `slug` из веб-версии или из экрана публикации.</Text>
      <TextField label="Slug" value={slug} onChangeText={setSlug} placeholder="abc123" />
      <Pressable
        style={styles.button}
        onPress={() => void loadShare(slug)}
      >
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Открыть</Text>}
      </Pressable>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {data ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{data.title}</Text>
          <Text style={styles.cardMeta}>Просмотры: {data.views}</Text>
          <FlatList
            data={data.messages}
            keyExtractor={(item) => String(item.id)}
            renderItem={({ item }) => (
              <View style={[styles.msg, item.role === "user" ? styles.user : styles.assistant]}>
                <Text style={styles.msgRole}>{item.role}</Text>
                <Text style={styles.msgText}>{item.content}</Text>
              </View>
            )}
          />
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  subtitle: { color: "#94a3b8", marginBottom: 12, lineHeight: 20 },
  button: {
    marginTop: 12,
    marginBottom: 12,
    backgroundColor: "#06b6d4",
    borderRadius: 14,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center"
  },
  buttonText: { color: "#fff", fontWeight: "700" },
  error: { color: "#fca5a5", marginBottom: 12 },
  card: { backgroundColor: "#111827", borderRadius: 18, padding: 16 },
  cardTitle: { color: "#fff", fontSize: 18, fontWeight: "700" },
  cardMeta: { color: "#94a3b8", marginTop: 6, marginBottom: 14 },
  msg: { borderRadius: 14, padding: 12, marginBottom: 8 },
  user: { backgroundColor: "#164e63" },
  assistant: { backgroundColor: "#1e293b" },
  msgRole: { color: "#67e8f9", fontSize: 12, marginBottom: 4, textTransform: "uppercase" },
  msgText: { color: "#e2e8f0" }
});
