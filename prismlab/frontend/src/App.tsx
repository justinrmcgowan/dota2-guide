import { useState, useEffect } from "react";
import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import MainPanel from "./components/layout/MainPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { useGsiStore, type GsiLiveState } from "./stores/gsiStore";

function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);

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
    <div className="h-screen flex flex-col bg-bg-primary text-gray-100 font-body">
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <MainPanel />
      </div>
    </div>
  );
}

export default App;
