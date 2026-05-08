"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Play, Square, Trash2, AlertCircle, Bot as BotIcon, Pencil, TrendingUp, TrendingDown } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { bots, trades, type Bot, type Performance, type DashboardSummary } from "@/lib/api";

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
  const [warnings, setWarnings] = useState<Record<string, string>>({});
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [list, summaryData] = await Promise.all([bots.list(), trades.summary()]);
      setBotList(list);
      setSummary(summaryData);
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
    const result = await bots.stop(id);
    if (result.warning) {
      setWarnings((prev) => ({ ...prev, [id]: result.warning! }));
    }
    await load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("このボットを削除しますか？")) return;
    await bots.delete(id);
    await load();
  };

  if (loading) return <div className="p-8 text-gray-400">読み込み中...</div>;

  const s = summary?.summary;
  const hasTrades = (s?.trade_count ?? 0) > 0;

  return (
    <div className="p-8 space-y-8">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">ダッシュボード</h1>
        <Link
          href="/dashboard/bots/new"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> ボット追加
        </Link>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* 全体サマリー */}
      {hasTrades && s && (
        <section>
          <h2 className="text-sm font-medium text-gray-400 mb-3">全体成績</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
              <p className="text-xs text-gray-500 mb-1">総損益</p>
              <p className={`text-xl font-bold ${s.total_pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {s.total_pnl >= 0 ? "+" : ""}{s.total_pnl.toLocaleString()}
              </p>
            </div>
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
              <p className="text-xs text-gray-500 mb-1">総取引数</p>
              <p className="text-xl font-bold">{s.trade_count}<span className="text-sm font-normal text-gray-500 ml-1">回</span></p>
            </div>
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
              <p className="text-xs text-gray-500 mb-1">勝率</p>
              <p className={`text-xl font-bold ${s.win_rate >= 50 ? "text-emerald-400" : "text-red-400"}`}>
                {s.win_rate.toFixed(1)}<span className="text-sm font-normal text-gray-500 ml-0.5">%</span>
              </p>
            </div>
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
              <p className="text-xs text-gray-500 mb-1">勝/負</p>
              <p className="text-xl font-bold">
                <span className="text-emerald-400">{s.win_count}</span>
                <span className="text-gray-600 mx-1">/</span>
                <span className="text-red-400">{s.trade_count - s.win_count}</span>
              </p>
            </div>
          </div>
        </section>
      )}

      {/* 日次損益グラフ */}
      {(summary?.daily_pnl.length ?? 0) > 0 && (
        <section>
          <h2 className="text-sm font-medium text-gray-400 mb-3">日次損益</h2>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={summary!.daily_pnl}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(d) => {
                    const dt = new Date(d);
                    return `${dt.getMonth() + 1}/${dt.getDate()}`;
                  }}
                  tick={{ fill: "#6b7280", fontSize: 11 }}
                />
                <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} width={50} />
                <Tooltip
                  formatter={(v) => [`${Number(v).toLocaleString()}`, "損益"]}
                  labelFormatter={(d) => new Date(d).toLocaleDateString("ja-JP")}
                  contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                  labelStyle={{ color: "#9ca3af" }}
                />
                <Bar dataKey="pnl" radius={[3, 3, 0, 0]}>
                  {summary!.daily_pnl.map((entry, i) => (
                    <Cell key={i} fill={entry.pnl >= 0 ? "#34d399" : "#f87171"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ボット一覧 */}
      <section>
        <h2 className="text-sm font-medium text-gray-400 mb-3">ボット</h2>
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
                  <div className="flex items-start justify-between">
                    <Link href={`/dashboard/bots/${bot.id}`} className="hover:opacity-80">
                      <p className="font-medium">{bot.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{bot.exchange} · {bot.symbol}</p>
                    </Link>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[bot.status]}`}>
                      {STATUS_LABELS[bot.status]}
                    </span>
                  </div>

                  {bot.error_message && (
                    <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">{bot.error_message}</p>
                  )}

                  {warnings[bot.id] && (
                    <div className="flex items-start gap-1.5 text-xs text-amber-400 bg-amber-500/10 rounded p-2">
                      <AlertCircle size={13} className="mt-0.5 shrink-0" />
                      <span>{warnings[bot.id]}</span>
                    </div>
                  )}

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

                  <div className="flex gap-2">
                    {bot.status === "running" ? (
                      <button onClick={() => handleStop(bot.id)}
                        className="flex-1 flex items-center justify-center gap-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg py-2 text-sm transition-colors">
                        <Square size={14} /> 停止
                      </button>
                    ) : (
                      <button onClick={() => handleStart(bot.id)}
                        className="flex-1 flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg py-2 text-sm transition-colors">
                        <Play size={14} /> 起動
                      </button>
                    )}
                    <Link href={`/dashboard/bots/${bot.id}/edit`}
                      className="p-2 text-gray-500 hover:text-indigo-400 hover:bg-gray-800 rounded-lg transition-colors">
                      <Pencil size={16} />
                    </Link>
                    <button onClick={() => handleDelete(bot.id)} disabled={bot.status === "running"}
                      className="p-2 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-30">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* 直近取引履歴 */}
      {(summary?.recent_trades.length ?? 0) > 0 && (
        <section>
          <h2 className="text-sm font-medium text-gray-400 mb-3">直近の取引履歴</h2>
          <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs border-b border-gray-800">
                    <th className="text-left px-5 py-3">日時</th>
                    <th className="text-left px-4 py-3">ボット</th>
                    <th className="text-left px-4 py-3">売買</th>
                    <th className="text-left px-4 py-3">通貨ペア</th>
                    <th className="text-right px-4 py-3">価格</th>
                    <th className="text-right px-5 py-3">損益</th>
                  </tr>
                </thead>
                <tbody>
                  {summary!.recent_trades.map((t) => (
                    <tr key={t.id} className="border-b border-gray-800/50 hover:bg-gray-800/40">
                      <td className="px-5 py-2.5 text-gray-400 text-xs">
                        {new Date(t.executed_at).toLocaleString("ja-JP")}
                      </td>
                      <td className="px-4 py-2.5 text-gray-300 text-xs">{t.bot_name}</td>
                      <td className="px-4 py-2.5">
                        <span className={`flex items-center gap-1 text-xs font-medium ${t.side === "buy" ? "text-emerald-400" : "text-red-400"}`}>
                          {t.side === "buy" ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                          {t.side === "buy" ? "買" : "売"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs">{t.symbol}</td>
                      <td className="px-4 py-2.5 text-right text-gray-300 text-xs">
                        {t.price.toLocaleString()}
                      </td>
                      <td className="px-5 py-2.5 text-right font-medium text-xs">
                        {t.pnl != null ? (
                          <span className={t.pnl >= 0 ? "text-emerald-400" : "text-red-400"}>
                            {t.pnl >= 0 ? "+" : ""}{t.pnl.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </span>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
