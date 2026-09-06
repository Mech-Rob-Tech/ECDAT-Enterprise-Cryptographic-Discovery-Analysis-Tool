import { useSyncExternalStore } from "react";

function subscribe(key: string, callback: () => void) {
  const handleStorage = (event: StorageEvent) => {
    if (
      event.storageArea === window.sessionStorage &&
      (event.key === key || event.key === null)
    ) {
      callback();
    }
  };

  window.addEventListener("storage", handleStorage);

  return () => window.removeEventListener("storage", handleStorage);
}

function getSnapshot(key: string) {
  return window.sessionStorage.getItem(key);
}

function getServerSnapshot() {
  return null;
}

export function useSessionStorageValue(key: string) {
  return useSyncExternalStore(
    (callback) => subscribe(key, callback),
    () => getSnapshot(key),
    getServerSnapshot
  );
}
