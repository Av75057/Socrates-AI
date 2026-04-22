import React from "react";
import { ActivityIndicator, View } from "react-native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "../store/authStore";
import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import ChatScreen from "../screens/chat/ChatScreen";
import HistoryScreen from "../screens/history/HistoryScreen";
import ConversationScreen from "../screens/history/ConversationScreen";
import SkillsScreen from "../screens/skills/SkillsScreen";
import ProfileScreen from "../screens/profile/ProfileScreen";
import SettingsScreen from "../screens/settings/SettingsScreen";
import PricingScreen from "../screens/pricing/PricingScreen";
import EducatorDashboardScreen from "../screens/educator/EducatorDashboardScreen";
import EducatorClassScreen from "../screens/educator/EducatorClassScreen";
import EducatorStudentScreen from "../screens/educator/EducatorStudentScreen";
import SubscriptionWebViewScreen from "../screens/pricing/SubscriptionWebViewScreen";
import PublicShareScreen from "../screens/share/PublicShareScreen";

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

function AppTabs() {
  const user = useAuthStore((s) => s.user);
  const isEducator = ["educator", "admin"].includes(String(user?.role || "").toLowerCase());

  return (
    <Tabs.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ color, size }) => {
          const map: Record<string, keyof typeof Ionicons.glyphMap> = {
            Chat: "chatbubble-ellipses-outline",
            History: "time-outline",
            Skills: "stats-chart-outline",
            Profile: "person-outline",
            Educator: "school-outline"
          };
          return <Ionicons name={map[route.name]} size={size} color={color} />;
        }
      })}
    >
      <Tabs.Screen name="Chat" component={ChatScreen} />
      <Tabs.Screen name="History" component={HistoryScreen} />
      <Tabs.Screen name="Skills" component={SkillsScreen} />
      {isEducator ? <Tabs.Screen name="Educator" component={EducatorDashboardScreen} /> : null}
      <Tabs.Screen name="Profile" component={ProfileScreen} />
    </Tabs.Navigator>
  );
}

export default function RootNavigator() {
  const { user, loading } = useAuthStore();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Stack.Navigator>
      {!user ? (
        <>
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ headerShown: false }} />
        </>
      ) : (
        <>
          <Stack.Screen name="HomeTabs" component={AppTabs} options={{ headerShown: false }} />
          <Stack.Screen name="Conversation" component={ConversationScreen} options={{ title: "Диалог" }} />
          <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: "Настройки" }} />
          <Stack.Screen name="Pricing" component={PricingScreen} options={{ title: "Подписка" }} />
          <Stack.Screen name="SubscriptionWebView" component={SubscriptionWebViewScreen} options={{ title: "Checkout" }} />
          <Stack.Screen name="PublicShare" component={PublicShareScreen} options={{ title: "Публичный диалог" }} />
          <Stack.Screen name="EducatorClass" component={EducatorClassScreen} options={{ title: "Класс" }} />
          <Stack.Screen name="EducatorStudent" component={EducatorStudentScreen} options={{ title: "Прогресс ученика" }} />
        </>
      )}
    </Stack.Navigator>
  );
}
