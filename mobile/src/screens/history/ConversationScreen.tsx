import React, { useEffect, useRef, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import Share from "react-native-share";
import ViewShot from "react-native-view-shot";
import { captureRef } from "react-native-view-shot";
import { fetchConversation, publishConversation, unpublishConversation } from "../../api/user";
import MessageBubble from "../../components/chat/MessageBubble";
import { ChatMessage } from "../../types";

export default function ConversationScreen({ route }: any) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [title, setTitle] = useState("Диалог");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [publicSlug, setPublicSlug] = useState<string | null>(null);
  const cardRef = useRef<any>(null);

  useEffect(() => {
    const id = Number(route.params?.id);
    fetchConversation(id).then((data) => {
      setConversationId(data.id);
      setTitle(data.title);
      setPublicSlug(data.public_slug || null);
      setMessages(
        (data.messages || []).map((m: any) => ({
          id: `db-${m.id}`,
          role: m.role === "tutor" ? "assistant" : "user",
          text: m.content,
          createdAt: Date.now()
        }))
      );
    });
  }, [route.params]);

  return (
    <Screen>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.actions}>
        <Pressable
          style={styles.action}
          onPress={async () => {
            if (!conversationId) return;
            const published = await publishConversation(conversationId);
            setPublicSlug(published.slug);
            await Share.open({ message: published.share_url });
          }}
        >
          <Text style={styles.actionText}>{publicSlug ? "Поделиться ссылкой" : "Опубликовать"}</Text>
        </Pressable>
        {publicSlug ? (
          <Pressable
            style={styles.action}
            onPress={async () => {
              if (!conversationId) return;
              await unpublishConversation(conversationId);
              setPublicSlug(null);
            }}
          >
            <Text style={styles.actionText}>Снять публикацию</Text>
          </Pressable>
        ) : null}
        <Pressable
          style={styles.action}
          onPress={async () => {
            const uri = await captureRef(cardRef, { format: "png", quality: 0.9 });
            await Share.open({ url: uri });
          }}
        >
          <Text style={styles.actionText}>Поделиться карточкой</Text>
        </Pressable>
      </View>
      <ViewShot ref={cardRef} options={{ format: "png", quality: 0.9 }}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Socrates AI</Text>
          <Text style={styles.cardSubtitle}>{title}</Text>
        </View>
      </ViewShot>
      <FlatList data={messages} keyExtractor={(item) => item.id} renderItem={({ item }) => <MessageBubble message={item} />} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 22, fontWeight: "800", marginBottom: 16 },
  actions: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 12 },
  action: {
    backgroundColor: "#1e293b",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  actionText: { color: "#fff", fontWeight: "600", fontSize: 12 },
  card: {
    backgroundColor: "#111827",
    borderRadius: 18,
    padding: 18,
    marginBottom: 14
  },
  cardTitle: { color: "#67e8f9", fontWeight: "800", fontSize: 18 },
  cardSubtitle: { color: "#fff", fontSize: 16, marginTop: 8 }
});
