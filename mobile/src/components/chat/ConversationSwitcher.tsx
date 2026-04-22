import React from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { ConversationSummary } from "../../types";

type Props = {
  visible: boolean;
  items: ConversationSummary[];
  activeId: number | null;
  onClose: () => void;
  onSelect: (id: number) => void;
  onNew: () => void;
};

export default function ConversationSwitcher({
  visible,
  items,
  activeId,
  onClose,
  onSelect,
  onNew
}: Props) {
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={() => null}>
          <View style={styles.header}>
            <Text style={styles.title}>Диалоги</Text>
            <Text style={styles.newLink} onPress={onNew}>
              Новый
            </Text>
          </View>
          <ScrollView>
            {items.map((item) => (
              <Pressable
                key={item.id}
                style={[styles.item, activeId === item.id && styles.itemActive]}
                onPress={() => onSelect(item.id)}
              >
                <Text style={styles.itemTitle}>{item.title}</Text>
                <Text style={styles.itemMeta}>{new Date(item.last_updated_at).toLocaleString()}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(2, 6, 23, 0.7)",
    justifyContent: "flex-end"
  },
  sheet: {
    maxHeight: "70%",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: "#0f172a",
    padding: 16
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12
  },
  title: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "800"
  },
  newLink: {
    color: "#67e8f9",
    fontWeight: "700"
  },
  item: {
    borderRadius: 16,
    backgroundColor: "#111827",
    padding: 14,
    marginBottom: 10
  },
  itemActive: {
    borderWidth: 1,
    borderColor: "#22d3ee"
  },
  itemTitle: {
    color: "#fff",
    fontWeight: "700"
  },
  itemMeta: {
    color: "#94a3b8",
    marginTop: 6
  }
});
