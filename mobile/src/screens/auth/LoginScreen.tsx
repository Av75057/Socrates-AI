import React, { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import PrimaryButton from "../../components/PrimaryButton";
import { useAuthStore } from "../../store/authStore";
import { apiErrorMessage } from "../../api/client";

export default function LoginScreen({ navigation }: any) {
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  return (
    <Screen contentStyle={styles.wrap}>
      <View style={styles.card}>
        <Text style={styles.title}>Socrates AI</Text>
        <Text style={styles.subtitle}>Вход в мобильное приложение</Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <TextField label="Email" value={email} onChangeText={setEmail} placeholder="you@example.com" />
        <TextField label="Пароль" value={password} onChangeText={setPassword} secureTextEntry />
        <PrimaryButton
          title="Войти"
          loading={loading}
          onPress={async () => {
            try {
              setLoading(true);
              setError("");
              await login(email.trim(), password);
            } catch (e) {
              setError(apiErrorMessage(e));
            } finally {
              setLoading(false);
            }
          }}
        />
        <Text style={styles.link} onPress={() => navigation.navigate("Register")}>
          Нет аккаунта? Регистрация
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: {
    justifyContent: "center"
  },
  card: {
    gap: 16,
    backgroundColor: "#020617",
    borderRadius: 24,
    padding: 20
  },
  title: {
    color: "#fff",
    fontSize: 28,
    fontWeight: "800"
  },
  subtitle: {
    color: "#94a3b8"
  },
  error: {
    color: "#fca5a5"
  },
  link: {
    color: "#67e8f9",
    textAlign: "center"
  }
});
