"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Play, Square, Trash2, AlertCircle, Bot as BotIcon } from "lucide-react";
import { bots, type Bot, type Performance } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  running: "bg-emerald-500/20 text-emerald-400",
  stopped: "bg-gray-500/20 text-gray-400",
  error: "bg-red-500/20 text-red-400",
};

const STATUS_LABELS: Record<string, string> = {
  running: "稼働中",
  stopped: "停止",
  error: "エラー",
};

export default function DashboardPage() {
  const [botList, setBotList] = useState<Bot[]>([]);
  const [performances, setPerformances] = useState<Record<string, Performance>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const list = await bots.list();
      setBotList(list);
      const perfResults = await Promise.allSettled(list.map((b) => bots.performance(b.id)));
      const perfMap: Record<string, Performance> = {};
      perfResults.forEach((r, i) => {
        if (r.status === "fulfilled") perfMap[list[i].id] = r.value;
      });
      setPerformances(perfMap);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みエラー");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleStart = async (id: string) => {
    await bots.start(id);
    await load();
  };

  const handleStop = async (id: string) => {
    await bots.stop(id);
    await load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("このボットを削除しますか？")) return;
    await bots.delete(id);
    await load();
  };

  if (loading) return <div className="p-8 text-gray-400">読み込み中...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">ダッシュボード</h1>
        <Link
          href="/dashboard/bots/new"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          ボット追加
        </Link>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 mb-4 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {botList.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <BotIcon size={48} className="mx-auto mb-4 opacity-30" />
          <p>ボットがまだありません</p>
          <Link href="/dashboard/bots/new" className="text-indigo-400 hover:underline mt-2 inline-block">
            最初のボットを作成する
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {botList.map((bot) => {
            const perf = performances[bot.id];
            return (
              <div key={bot.id} className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
                {/* ヘッダー */}
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{bot.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{bot.exchange} · {bot.symbol}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[bot.status]}`}>
                    {STATUS_LABELS[bot.status]}
                  </span>
                </div>

                {/* エラーメッセージ */}
                {bot.error_message && (
                  <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">{bot.error_message}</p>
                )}

                {/* 成績 */}
                {perf && (
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-gray-800 rounded-lg p-2">
                      <p className="text-xs text-gray-500">損益</p>
                      <p className={`text-sm font-semibold ${perf.total_pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {perf.total_pnl >= 0 ? "+" : ""}{perf.total_pnl.toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-2">
                      <p className="text-xs text-gray-500">取引数</p>
                      <p className="text-sm font-semibold">{perf.trade_count}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-2">
                      <p className="text-xs text-gray-500">勝率</p>
                      <p className="text-sm font-semibold">{perf.win_rate.toFixed(1)}%</p>
                    </div>
                  </div>
                )}

                {/* 操作ボタン */}
                <div className="flex gap-2">
                  {bot.status === "running" ? (
                    <button
                      onClick={() => handleStop(bot.id)}
                      className="flex-1 flex items-center justify-center gap-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg py-2 text-sm transition-colors"
                    >
                      <Square size={14} /> 停止
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStart(bot.id)}
                      className="flex-1 flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg py-2 text-sm transition-colors"
                    >
                      <Play size={14} /> 起動
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(bot.id)}
                    disabled={bot.status === "running"}
                    className="p-2 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-30"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
