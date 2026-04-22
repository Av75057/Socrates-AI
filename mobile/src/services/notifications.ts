import * as Notifications from "expo-notifications";

export async function bootstrapNotifications() {
  await Notifications.requestPermissionsAsync();
}

export async function scheduleDailyChallengeReminder() {
  await Notifications.cancelAllScheduledNotificationsAsync();
  await Notifications.scheduleNotificationAsync({
    content: {
      title: "Socrates AI",
      body: "Пора пройти ежедневный вызов."
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.DAILY,
      hour: 19,
      minute: 0
    }
  });
}
