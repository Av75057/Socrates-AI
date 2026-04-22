import React, { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import PrimaryButton from "../../components/PrimaryButton";
import { useAuthStore } from "../../store/authStore";
import { apiErrorMessage } from "../../api/client";

export default function RegisterScreen({ navigation }: any) {
  const register = useAuthStore((s) => s.register);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  return (
    <Screen contentStyle={styles.wrap}>
      <View style={styles.card}>
        <Text style={styles.title}>Регистрация</Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <TextField label="Имя" value={fullName} onChangeText={setFullName} />
        <TextField label="Email" value={email} onChangeText={setEmail} />
        <TextField label="Пароль" value={password} onChangeText={setPassword} secureTextEntry />
        <PrimaryButton
          title="Создать аккаунт"
          loading={loading}
          onPress={async () => {
            try {
              setLoading(true);
              setError("");
              await register(email.trim(), password, fullName);
            } catch (e) {
              setError(apiErrorMessage(e));
            } finally {
              setLoading(false);
            }
          }}
        />
        <Text style={styles.link} onPress={() => navigation.goBack()}>
          Уже есть аккаунт? Войти
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: { justifyContent: "center" },
  card: { gap: 16, backgroundColor: "#020617", borderRadius: 24, padding: 20 },
  title: { color: "#fff", fontSize: 28, fontWeight: "800" },
  error: { color: "#fca5a5" },
  link: { color: "#67e8f9", textAlign: "center" }
});
