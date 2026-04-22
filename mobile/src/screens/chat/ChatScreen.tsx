import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import { useChatStore } from "../../store/chatStore";
import MessageBubble from "../../components/chat/MessageBubble";
import ChatComposer from "../../components/chat/ChatComposer";
import QuickActions from "../../components/chat/QuickActions";
import ExplainPromptPanel from "../../components/chat/ExplainPromptPanel";
import ConversationSwitcher from "../../components/chat/ConversationSwitcher";

export default function ChatScreen({ route }: any) {
  const {
    messages,
    loading,
    sessionId,
    conversationId,
    conversationTitle,
    conversations,
    offline,
    bootstrap,
    loadConversations,
    openConversation,
    startNewConversation,
    sendMessage,
    flushQueue
  } = useChatStore();
  const [switcherOpen, setSwitcherOpen] = useState(false);

  useEffect(() => {
    void bootstrap();
    void loadConversations();
    void flushQueue();
  }, [bootstrap, loadConversations, flushQueue]);

  useEffect(() => {
    const prompt = route?.params?.assignmentPrompt;
    const assignmentId = route?.params?.assignmentId;
    if (prompt && assignmentId && messages.length === 0) {
      void sendMessage(prompt, assignmentId);
    }
  }, [messages.length, route?.params, sendMessage]);

  return (
    <Screen scroll={false} contentStyle={styles.wrap}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Чат</Text>
          <Pressable onPress={() => setSwitcherOpen(true)}>
            <Text style={styles.subtitle}>{conversationTitle || "Новый диалог"}</Text>
          </Pressable>
        </View>
        {offline ? <Text style={styles.offline}>Оффлайн</Text> : null}
      </View>
      <ConversationSwitcher
        visible={switcherOpen}
        items={conversations}
        activeId={conversationId}
        onClose={() => setSwitcherOpen(false)}
        onSelect={(id) => {
          void openConversation(id);
          setSwitcherOpen(false);
        }}
        onNew={() => {
          startNewConversation();
          setSwitcherOpen(false);
        }}
      />
      <ExplainPromptPanel sessionId={sessionId} onExplain={() => void sendMessage("Объясни проще")} />
      <QuickActions
        onPress={(id) => {
          if (id === "hint") void sendMessage("Дай подсказку");
          if (id === "simpler") void sendMessage("Объясни проще");
          if (id === "dontknow") void sendMessage("Не знаю");
        }}
      />
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.list}
      />
      {loading ? (
        <View style={styles.typing}>
          <ActivityIndicator color="#67e8f9" />
          <Text style={styles.typingText}>Тьютор печатает…</Text>
        </View>
      ) : null}
      <ChatComposer onSend={(text) => void sendMessage(text)} loading={loading} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: { backgroundColor: "#0f172a" },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8
  },
  title: { color: "#fff", fontSize: 28, fontWeight: "800" },
  subtitle: { color: "#67e8f9", marginTop: 2, fontWeight: "600" },
  offline: {
    color: "#fbbf24",
    fontWeight: "700"
  },
  list: {
    paddingVertical: 8
  },
  typing: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8
  },
  typingText: { color: "#94a3b8" }
});
