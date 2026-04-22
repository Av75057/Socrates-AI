import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

type Props = {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  secureTextEntry?: boolean;
  multiline?: boolean;
  placeholder?: string;
};

export default function TextField(props: Props) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{props.label}</Text>
      <TextInput
        value={props.value}
        onChangeText={props.onChangeText}
        secureTextEntry={props.secureTextEntry}
        multiline={props.multiline}
        placeholder={props.placeholder}
        placeholderTextColor="#94a3b8"
        style={[styles.input, props.multiline && styles.multiline]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 8
  },
  label: {
    color: "#cbd5e1",
    fontSize: 12,
    textTransform: "uppercase"
  },
  input: {
    backgroundColor: "#111827",
    color: "#f8fafc",
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: "#334155"
  },
  multiline: {
    minHeight: 96,
    textAlignVertical: "top"
  }
});
