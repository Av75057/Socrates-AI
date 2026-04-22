import React, { useEffect } from "react";
import { NavigationContainer, DarkTheme, DefaultTheme } from "@react-navigation/native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import * as Notifications from "expo-notifications";
import * as Sentry from "@sentry/react-native";
import RootNavigator from "./src/navigation/RootNavigator";
import { useThemeStore } from "./src/store/themeStore";
import { useAuthStore } from "./src/store/authStore";
import { bootstrapNotifications } from "./src/services/notifications";

Sentry.init({
  dsn: "",
  enabled: false
});

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false
  })
});

export default function App() {
  const theme = useThemeStore((s) => s.theme);
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    void hydrate();
    void bootstrapNotifications();
  }, [hydrate]);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <NavigationContainer theme={theme === "dark" ? DarkTheme : DefaultTheme}>
          <StatusBar style={theme === "dark" ? "light" : "dark"} />
          <RootNavigator />
        </NavigationContainer>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
