import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import PrimaryButton from "../../components/PrimaryButton";
import { createClass, listClasses } from "../../api/educator";

export default function EducatorDashboardScreen({ navigation }: any) {
  const [classes, setClasses] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const load = async () => {
    setClasses(await listClasses());
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <Screen>
      <Text style={styles.title}>Панель учителя</Text>
      <View style={styles.hero}>
        <Text style={styles.heroLabel}>Классы</Text>
        <Text style={styles.heroValue}>{classes.length}</Text>
      </View>
      {classes.map((item) => (
        <Pressable
          key={item.id}
          style={styles.card}
          onPress={() => navigation.navigate("EducatorClass", { id: item.id, title: item.name })}
        >
          <Text style={styles.cardTitle}>{item.name}</Text>
          <Text style={styles.cardMeta}>
            {item.students_count} учеников · {item.assignments_count} заданий
          </Text>
        </Pressable>
      ))}
      <View style={styles.form}>
        <Text style={styles.formTitle}>Создать класс</Text>
        <TextField label="Название" value={name} onChangeText={setName} />
        <TextField label="Описание" value={description} onChangeText={setDescription} multiline />
        <PrimaryButton
          title="Создать"
          onPress={async () => {
            await createClass({ name, description });
            setName("");
            setDescription("");
            await load();
          }}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  hero: { backgroundColor: "#1e293b", borderRadius: 20, padding: 18, marginBottom: 16 },
  heroLabel: { color: "#cbd5e1" },
  heroValue: { color: "#fff", fontSize: 34, fontWeight: "800", marginTop: 8 },
  card: { backgroundColor: "#111827", borderRadius: 18, padding: 16, marginBottom: 12 },
  cardTitle: { color: "#fff", fontSize: 18, fontWeight: "700" },
  cardMeta: { color: "#94a3b8", marginTop: 8 },
  form: { gap: 14, marginTop: 10, paddingTop: 8 },
  formTitle: { color: "#fff", fontSize: 20, fontWeight: "700" }
});
