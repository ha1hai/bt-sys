"use client";

import { useEffect, useState } from "react";
import { Trash2, Plus, CheckCircle, AlertCircle } from "lucide-react";
import { exchanges, type ExchangeKey } from "@/lib/api";

export default function SettingsPage() {
  const [keys, setKeys] = useState<ExchangeKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({ exchange: "bitflyer", api_key: "", api_secret: "" });

  const load = async () => {
    try {
      setKeys(await exchanges.list());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setAdding(true);
    try {
      await exchanges.add(form.exchange, form.api_key, form.api_secret);
      setForm({ exchange: "bitflyer", api_key: "", api_secret: "" });
      setSuccess("APIキーを登録しました");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "登録に失敗しました");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id: string) => {
    if (!confirm("このAPIキーを削除しますか？")) return;
    await exchanges.remove(id);
    await load();
  };

  return (
    <div className="p-8 max-w-xl space-y-8">
      <h1 className="text-xl font-semibold">設定</h1>

      {/* 登録済みAPIキー一覧 */}
      <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-3">
        <h2 className="text-sm font-medium text-gray-400">取引所 APIキー</h2>
        {loading ? (
          <p className="text-sm text-gray-500">読み込み中...</p>
        ) : keys.length === 0 ? (
          <p className="text-sm text-gray-500">登録済みのAPIキーがありません</p>
        ) : (
          keys.map((k) => (
            <div key={k.id} className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-3">
              <div>
                <p className="text-sm font-medium capitalize">{k.exchange}</p>
                <p className="text-xs text-gray-500">
                  登録日: {new Date(k.created_at).toLocaleDateString("ja-JP")}
                </p>
              </div>
              <button onClick={() => handleRemove(k.id)}
                className="p-1.5 text-gray-500 hover:text-red-400 rounded-lg hover:bg-gray-700 transition-colors">
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </section>

      {/* APIキー追加フォーム */}
      <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
        <h2 className="text-sm font-medium text-gray-400">APIキーを追加</h2>
        <form onSubmit={handleAdd} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">取引所</label>
            <select value={form.exchange} onChange={(e) => setForm((f) => ({ ...f, exchange: e.target.value }))}
              className="input">
              <option value="bitflyer">bitFlyer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">API Key</label>
            <input value={form.api_key} onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
              required placeholder="APIキーを入力" className="input" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">API Secret</label>
            <input type="password" value={form.api_secret}
              onChange={(e) => setForm((f) => ({ ...f, api_secret: e.target.value }))}
              required placeholder="APIシークレットを入力" className="input" />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <AlertCircle size={14} /> {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle size={14} /> {success}
            </div>
          )}

          <button type="submit" disabled={adding}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg px-4 py-2 text-sm font-medium transition-colors">
            <Plus size={16} />
            {adding ? "接続確認中..." : "APIキーを登録"}
          </button>
        </form>
      </section>
    </div>
  );
}
