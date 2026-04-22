import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import Share from "react-native-share";
import ViewShot, { captureRef } from "react-native-view-shot";
import Screen from "../../components/Screen";
import TextField from "../../components/TextField";
import PrimaryButton from "../../components/PrimaryButton";
import { useAuthStore } from "../../store/authStore";
import { deleteAvatar, fetchAssignments, fetchEducators, fetchSubscription, updateMe, uploadAvatar } from "../../api/user";
import { fetchGamificationMe } from "../../api/gamification";
import { scheduleDailyChallengeReminder } from "../../services/notifications";
import { apiErrorMessage, resolveApiUrl } from "../../api/client";
import { SubscriptionInfo } from "../../types";

export default function ProfileScreen({ navigation }: any) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const refreshUser = useAuthStore((s) => s.refreshUser);
  const [educators, setEducators] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [gamification, setGamification] = useState<any>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [error, setError] = useState("");
  const shareCardRef = React.useRef<any>(null);
  const avatarUri = resolveApiUrl(user?.avatar_url);
  const initials = useMemo(() => {
    const source = (user?.full_name || user?.email || "?").trim();
    if (!source) return "?";
    return source
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || "")
      .join("");
  }, [user?.email, user?.full_name]);

  useEffect(() => {
    setFullName(user?.full_name || "");
  }, [user?.full_name]);

  useEffect(() => {
    let active = true;
    setLoadingMeta(true);
    Promise.allSettled([fetchEducators(), fetchAssignments(), fetchGamificationMe(), fetchSubscription()])
      .then((results) => {
        if (!active) return;
        setEducators(results[0].status === "fulfilled" ? results[0].value : []);
        setAssignments(results[1].status === "fulfilled" ? results[1].value : []);
        setGamification(results[2].status === "fulfilled" ? results[2].value : null);
        setSubscription(results[3].status === "fulfilled" ? results[3].value : null);
      })
      .finally(() => {
        if (active) setLoadingMeta(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function saveProfile() {
    try {
      setSavingProfile(true);
      setError("");
      await updateMe({ full_name: fullName.trim() || null });
      await refreshUser();
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSavingProfile(false);
    }
  }

  async function pickAvatar() {
    try {
      setUploadingAvatar(true);
      setError("");
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setError("Нет доступа к галерее.");
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85
      });
      if (result.canceled || !result.assets?.length) return;
      const asset = result.assets[0];
      await uploadAvatar({
        uri: asset.uri,
        fileName: asset.fileName,
        mimeType: asset.mimeType
      });
      await refreshUser();
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setUploadingAvatar(false);
    }
  }

  async function removeAvatar() {
    try {
      setUploadingAvatar(true);
      setError("");
      await deleteAvatar();
      await refreshUser();
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setUploadingAvatar(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>Профиль</Text>
      <View style={styles.card}>
        <View style={styles.identityRow}>
          {avatarUri ? (
            <Image source={{ uri: avatarUri }} style={styles.avatarImage} />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarFallbackText}>{initials}</Text>
            </View>
          )}
          <View style={styles.identityText}>
            <Text style={styles.name}>{user?.full_name || user?.email}</Text>
            <Text style={styles.meta}>{user?.email}</Text>
            <Text style={styles.meta}>Роль: {user?.role}</Text>
            <Text style={styles.meta}>
              Тариф: {subscription ? `${subscription.plan} · ${subscription.status}` : "Free"}
            </Text>
          </View>
        </View>
        <View style={styles.avatarActions}>
          <PrimaryButton title={uploadingAvatar ? "Загружаем..." : "Выбрать аватар"} onPress={() => void pickAvatar()} loading={uploadingAvatar} />
          {avatarUri ? (
            <Pressable style={styles.secondaryAction} onPress={() => void removeAvatar()} disabled={uploadingAvatar}>
              <Text style={styles.secondaryActionText}>Удалить аватар</Text>
            </Pressable>
          ) : null}
        </View>
        <TextField label="Имя" value={fullName} onChangeText={setFullName} placeholder="Как к вам обращаться" />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <PrimaryButton title="Сохранить профиль" onPress={() => void saveProfile()} loading={savingProfile} />
        <Text style={styles.hint}>Аватар сохраняется на текущем backend и подтягивается в профиль после refresh.</Text>
      </View>
      <ViewShot ref={shareCardRef} options={{ format: "png", quality: 0.9 }}>
        <View style={styles.shareCard}>
          <Text style={styles.shareBrand}>Socrates AI</Text>
          <Text style={styles.shareTitle}>Мой прогресс</Text>
          <Text style={styles.shareStat}>Очки мудрости: {gamification?.wisdom_points ?? 0}</Text>
          <Text style={styles.shareStat}>Уровень: {gamification?.level ?? 1}</Text>
        </View>
      </ViewShot>
      <Pressable style={styles.action} onPress={() => navigation.navigate("Settings")}>
        <Text style={styles.actionText}>Настройки</Text>
      </Pressable>
      <Pressable style={styles.action} onPress={() => navigation.navigate("Pricing")}>
        <Text style={styles.actionText}>Free / Pro</Text>
      </Pressable>
      <Pressable
        style={styles.action}
        onPress={() => navigation.navigate("PublicShare")}
      >
        <Text style={styles.actionText}>Открыть публичный диалог по slug</Text>
      </Pressable>
      <Pressable style={styles.action} onPress={() => void scheduleDailyChallengeReminder()}>
        <Text style={styles.actionText}>Включить daily challenge reminder</Text>
      </Pressable>
      <Pressable
        style={styles.action}
        onPress={async () => {
          const uri = await captureRef(shareCardRef, { format: "png", quality: 0.9 });
          await Share.open({ url: uri });
        }}
      >
        <Text style={styles.actionText}>Поделиться достижением</Text>
      </Pressable>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Мои учителя</Text>
        {loadingMeta ? <ActivityIndicator color="#67e8f9" style={styles.loader} /> : null}
        {!loadingMeta && educators.length === 0 ? <Text style={styles.empty}>Пока нет привязанных учителей.</Text> : null}
        {educators.map((item) => (
          <Text key={`${item.id}-${item.class_name}`} style={styles.line}>
            {item.full_name || item.email} · {item.class_name}
          </Text>
        ))}
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Активные задания</Text>
        {!loadingMeta && assignments.length === 0 ? <Text style={styles.empty}>Активных заданий нет.</Text> : null}
        {assignments.map((item) => (
          <Pressable
            key={item.id}
            style={styles.assignment}
            onPress={() =>
              navigation.navigate("HomeTabs", {
                screen: "Chat",
                params: { assignmentId: item.id, assignmentPrompt: item.prompt }
              })
            }
          >
            <Text style={styles.assignmentTitle}>{item.title}</Text>
            <Text style={styles.assignmentText}>{item.prompt}</Text>
          </Pressable>
        ))}
      </View>
      <Pressable style={[styles.action, styles.logout]} onPress={() => void logout()}>
        <Text style={styles.actionText}>Выйти</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: "#fff", fontSize: 28, fontWeight: "800", marginBottom: 16 },
  card: { backgroundColor: "#111827", borderRadius: 18, padding: 16, marginBottom: 12, gap: 12 },
  identityRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  identityText: { flex: 1 },
  avatarFallback: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0f766e"
  },
  avatarImage: { width: 56, height: 56, borderRadius: 28, backgroundColor: "#0f172a" },
  avatarFallbackText: { color: "#ecfeff", fontSize: 22, fontWeight: "800" },
  avatarActions: { gap: 10 },
  name: { color: "#fff", fontSize: 20, fontWeight: "700" },
  meta: { color: "#94a3b8", marginTop: 4 },
  error: { color: "#fca5a5" },
  hint: { color: "#94a3b8", fontSize: 12, lineHeight: 18 },
  secondaryAction: {
    backgroundColor: "#0f172a",
    borderRadius: 14,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#334155"
  },
  secondaryActionText: { color: "#cbd5e1", fontWeight: "600" },
  shareCard: {
    backgroundColor: "#0f766e",
    borderRadius: 18,
    padding: 18,
    marginBottom: 12
  },
  shareBrand: { color: "#99f6e4", fontWeight: "800" },
  shareTitle: { color: "#fff", fontSize: 20, fontWeight: "800", marginTop: 8 },
  shareStat: { color: "#ecfeff", marginTop: 8, fontSize: 15 },
  action: { backgroundColor: "#1e293b", borderRadius: 16, padding: 14, marginBottom: 10 },
  actionText: { color: "#fff", fontWeight: "600" },
  section: { marginTop: 18, gap: 10 },
  sectionTitle: { color: "#fff", fontSize: 18, fontWeight: "700" },
  loader: { marginTop: 4 },
  empty: { color: "#94a3b8" },
  line: { color: "#cbd5e1" },
  assignment: { backgroundColor: "#111827", borderRadius: 16, padding: 14 },
  assignmentTitle: { color: "#fff", fontWeight: "700" },
  assignmentText: { color: "#94a3b8", marginTop: 6 },
  logout: { backgroundColor: "#7f1d1d", marginTop: 18 }
});
