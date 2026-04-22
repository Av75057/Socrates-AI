import Constants from "expo-constants";

const extra = Constants.expoConfig?.extra ?? {};
const DEFAULT_API_URL = "http://127.0.0.1:8000";

function resolveApiUrl() {
  const configuredUrl = String(extra.apiUrl || DEFAULT_API_URL).replace(/\/$/, "");

  if (!__DEV__) {
    return configuredUrl;
  }

  try {
    const parsed = new URL(configuredUrl);
    if (!["127.0.0.1", "localhost"].includes(parsed.hostname)) {
      return configuredUrl;
    }

    const expoHostUri = Constants.expoConfig?.hostUri || Constants.platform?.hostUri;
    const expoHost = expoHostUri?.split(":")[0];
    if (!expoHost) {
      return configuredUrl;
    }

    parsed.hostname = expoHost;
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return configuredUrl;
  }
}

export const API_URL = resolveApiUrl();
export const APP_NAME = "Socrates AI";
