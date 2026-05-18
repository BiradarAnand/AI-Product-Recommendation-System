import { useEffect, useState } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "https://ai-product-recommendation-system-by60.onrender.com//api" });

export default function SearchHistoryDropdown({ onSelect, onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem("token");

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      const res = await API.get("/search-history?limit=10", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(res.data.queries || []);
    } catch (e) {
      console.log("Failed to load search history:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (query) => {
    onSelect(query);
  };

  const handleClear = async () => {
    try {
      await API.delete("/search-history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory([]);
    } catch (e) {
      console.log("Failed to clear history:", e);
    }
  };

  if (loading || history.length === 0) {
    return null;
  }

  return (
    <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Recent Searches</p>
      </div>

      <div className="max-h-64 overflow-y-auto">
        {history.map((query, idx) => (
          <button
            key={idx}
            onClick={() => handleSelect(query)}
            className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors flex items-center gap-3 border-b border-gray-100 last:border-b-0"
          >
            <span className="text-gray-400">🕐</span>
            <span className="text-gray-700 text-sm truncate">{query}</span>
          </button>
        ))}
      </div>

      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
        <button
          onClick={handleClear}
          className="w-full text-left text-xs text-gray-500 hover:text-gray-700 font-medium py-1 transition-colors"
        >
          Clear history
        </button>
      </div>
    </div>
  );
}