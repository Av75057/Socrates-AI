import React from "react";
import { StyleSheet, Text, View } from "react-native";
import Markdown from "react-native-markdown-display";
import { ChatMessage } from "../../types";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <View style={[styles.row, isUser ? styles.rowUser : styles.rowAssistant]}>
      <View style={[styles.bubble, isUser ? styles.user : styles.assistant]}>
        {isUser ? (
          <Text style={styles.userText}>{message.text}</Text>
        ) : (
          <Markdown style={markdownStyles}>{message.text}</Markdown>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    marginVertical: 6
  },
  rowUser: {
    alignItems: "flex-end"
  },
  rowAssistant: {
    alignItems: "flex-start"
  },
  bubble: {
    maxWidth: "86%",
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10
  },
  user: {
    backgroundColor: "#0891b2"
  },
  assistant: {
    backgroundColor: "#1e293b"
  },
  userText: {
    color: "#ffffff",
    fontSize: 15
  }
});

const markdownStyles = {
  body: {
    color: "#e2e8f0",
    fontSize: 15
  }
};
