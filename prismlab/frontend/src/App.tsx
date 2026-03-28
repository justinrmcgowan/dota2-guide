import { useState, useEffect, useCallback } from "react";
import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import MainPanel from "./components/layout/MainPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { useGameIntelligence } from "./hooks/useGameIntelligence";
import { useLiveDraft } from "./hooks/useLiveDraft";
import { useHeroes } from "./hooks/useHeroes";
import { useScreenshotPaste } from "./hooks/useScreenshotPaste";
import { useGsiStore, type GsiLiveState } from "./stores/gsiStore";
import { useScreenshotStore } from "./stores/screenshotStore";
import SettingsPanel from "./components/settings/SettingsPanel";
import AutoRefreshToast from "./components/toast/AutoRefreshToast";
import ScreenshotParser from "./components/screenshot/ScreenshotParser";

function App() {
  const { heroes } = useHeroes();
  useGameIntelligence(heroes);
  const { fetchDraft, isPolling } = useLiveDraft(heroes);

  const [settingsOpen, setSettingsOpen] = useState(false);

  // Screenshot paste handler -- opens modal with image and auto-triggers parse
  const openScreenshotModal = useCallback(
    (imageBase64: string, mimeType: string) => {
      useScreenshotStore.getState().openModal(imageBase64, mimeType);
    },
    [],
  );
  useScreenshotPaste(openScreenshotModal);

  const wsUrl = `ws${window.location.protocol === "https:" ? "s" : ""}://${window.location.host}/ws`;
  const { status, lastMessage } = useWebSocket(wsUrl);

  useEffect(() => {
    useGsiStore.getState().setWsStatus(status);
  }, [status]);

  useEffect(() => {
    if (
      lastMessage &&
      typeof lastMessage === "object" &&
      "type" in lastMessage &&
      (lastMessage as { type: string }).type === "game_state"
    ) {
      useGsiStore
        .getState()
        .updateLiveState(
          (lastMessage as { type: string; data: GsiLiveState }).data,
        );
    }
  }, [lastMessage]);

  return (
    <div className="h-screen flex flex-col bg-surface text-on-surface font-body noise-overlay relative">
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      <div className="flex flex-1 overflow-hidden relative z-10">
        <Sidebar />
        <MainPanel />
      </div>
      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
      <AutoRefreshToast />
      <ScreenshotParser heroes={heroes} />
    </div>
  );
}

export default App;
