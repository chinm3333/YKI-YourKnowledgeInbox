import { useCallback, useEffect, useState } from "react";
import IngestForm from "./components/IngestForm.jsx";
import ItemList from "./components/ItemList.jsx";
import QueryPanel from "./components/QueryPanel.jsx";
import { listItems } from "./api";

export default function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [apiOk, setApiOk] = useState(null);
  const [notice, setNotice] = useState(null);

  const refresh = useCallback(async () => {
    setListError("");
    try {
      const data = await listItems();
      setItems(data.items);
      setApiOk(true);
    } catch (error) {
      setListError(error.message);
      setApiOk(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), 3200);
    return () => clearTimeout(timer);
  }, [notice]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="mark" aria-hidden="true" />
          <div>
            <strong>Knowledge Inbox</strong>
            <span>Private RAG workspace</span>
          </div>
        </div>
        <div className="top-meta">
          <span className={`status ${apiOk ? "on" : apiOk === false ? "off" : ""}`}>
            {apiOk ? "API connected" : apiOk === false ? "API offline" : "Checking API"}
          </span>
          <span className="count">{items.length} sources</span>
        </div>
      </header>

      {listError && (
        <div className="banner" role="alert">
          <span>{listError}</span>
          <button type="button" className="text-btn" onClick={refresh}>
            Retry
          </button>
        </div>
      )}

      <main className="workspace">
        <section className="rail">
          <IngestForm
            onIngested={() => {
              refresh();
              setNotice("Saved to inbox");
            }}
          />
          <ItemList
            items={items}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDeleted={(id) => {
              setItems((current) => current.filter((item) => item.id !== id));
              if (selectedId === id) setSelectedId(null);
              setNotice("Source removed");
            }}
            onError={setListError}
            loading={loading}
          />
        </section>
        <QueryPanel onHighlight={setSelectedId} hasSources={items.length > 0} />
      </main>

      {notice && <div className="toast">{notice}</div>}
    </div>
  );
}
