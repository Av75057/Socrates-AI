import React, { useEffect, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import { deleteConversation, listConversations } from "../../api/user";
import { ConversationSummary } from "../../types";
import { apiErrorMessage } from "../../api/client";

export default function HistoryScreen({ navigation }: any) {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await listConversations());
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const filtered = items.filter((item) => item.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <Screen>
      <Text style={styles.title}>История</Text>
      <TextField label="Поиск" value={query} onChangeText={setQuery} placeholder="По названию диалога" />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <Pressable style={styles.card} onPress={() => navigation.navigate("Conversation", { id: item.id })}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.cardMeta}>{new Date(item.last_updated_at).toLocaleString()}</Text>
            <Text
              style={styles.delete}
              onPress={async () => {
                await deleteConversation(item.id);
                await load();
              }}
            >
              Удалить
            </Text>
          </Pressable>
        )}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  error: { color: "#fca5a5", marginVertical: 12 },
  card: {
    borderRadius: 18,
    backgroundColor: "#111827",
    padding: 16,
    marginBottom: 12
  },
  cardTitle: { color: "#fff", fontSize: 16, fontWeight: "700" },
  cardMeta: { color: "#94a3b8", marginTop: 6 },
  delete: { color: "#f87171", marginTop: 10 }
});
