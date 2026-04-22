import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import Screen from "../../components/Screen";
import PrimaryButton from "../../components/PrimaryButton";
import { fetchSubscription } from "../../api/user";
import { apiErrorMessage } from "../../api/client";
import { SubscriptionInfo } from "../../types";

const STRIPE_CHECKOUT_URL = "https://example.com/stripe-checkout";

export default function PricingScreen({ navigation }: any) {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSubscription().then(setSubscription).catch((e) => setError(apiErrorMessage(e)));
  }, []);

  return (
    <Screen>
      <Text style={styles.title}>Подписка</Text>
      <View style={styles.status}>
        <Text style={styles.statusLabel}>Текущий статус</Text>
        <Text style={styles.statusValue}>{subscription ? subscription.plan : "..."}</Text>
        <Text style={styles.statusHint}>
          {subscription
            ? `Статус: ${subscription.status}${subscription.current_period_end ? ` · до ${subscription.current_period_end}` : ""}`
            : "Загружаем статус подписки с backend."}
        </Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {!subscription && !error ? <ActivityIndicator color="#67e8f9" style={styles.loader} /> : null}
      </View>
      <View style={styles.card}>
        <Text style={styles.plan}>Free</Text>
        <Text style={styles.desc}>Базовый доступ, ограничение по использованию.</Text>
      </View>
      <View style={[styles.card, styles.pro]}>
        <Text style={styles.plan}>Pro</Text>
        <Text style={styles.desc}>Больше диалогов, приоритетные модели, расширенная аналитика.</Text>
      </View>
      <PrimaryButton
        title="Открыть Stripe Checkout"
        onPress={() => navigation.navigate("SubscriptionWebView", { url: STRIPE_CHECKOUT_URL })}
      />
      <Text style={styles.footnote}>
        Перед production нужно подставить реальный checkout URL или backend endpoint создания checkout session.
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  status: { backgroundColor: "#0f172a", borderRadius: 18, padding: 18, marginBottom: 14, borderWidth: 1, borderColor: "#1e293b" },
  statusLabel: { color: "#94a3b8", textTransform: "uppercase", fontSize: 12, marginBottom: 8 },
  statusValue: { color: "#fff", fontSize: 24, fontWeight: "800" },
  statusHint: { color: "#cbd5e1", marginTop: 8, lineHeight: 20 },
  error: { color: "#fca5a5", marginTop: 10 },
  loader: { marginTop: 10 },
  card: { backgroundColor: "#111827", borderRadius: 18, padding: 18, marginBottom: 12 },
  pro: { borderWidth: 1, borderColor: "#f59e0b" },
  plan: { color: "#fff", fontSize: 20, fontWeight: "700" },
  desc: { color: "#cbd5e1", marginTop: 8 },
  footnote: { color: "#94a3b8", marginTop: 12, lineHeight: 18 }
});
