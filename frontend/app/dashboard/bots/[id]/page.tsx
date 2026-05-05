"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Pencil, TrendingUp, TrendingDown } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { bots, type Bot, type BacktestResult } from "@/lib/api";

const PERIODS = [
  { value: "1m", label: "1ヶ月" },
  { value: "3m", label: "3ヶ月" },
  { value: "6m", label: "6ヶ月" },
] as const;

type Period = "1m" | "3m" | "6m";

export default function BotDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [bot, setBot] = useState<Bot | null>(null);
  const [tab, setTab] = useState<"performance" | "backtest">("backtest");
  const [period, setPeriod] = useState<Period>("1m");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    bots.get(id).then(setBot).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  const handleBacktest = async () => {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const r = await bots.backtest(id, period);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-400">読み込み中...</div>;
  if (!bot) return <div className="p-8 text-red-400">{error || "ボットが見つかりません"}</div>;

  const params = bot.strategy_params as Record<string, unknown>;

  return (
    <div className="p-8 max-w-3xl">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-gray-400 hover:text-gray-200">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-xl font-semibold">{bot.name}</h1>
            <p className="text-xs text-gray-500">{bot.exchange} · {bot.symbol} · {bot.strategy.toUpperCase()}</p>
          </div>
        </div>
        <Link href={`/dashboard/bots/${id}/edit`}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-indigo-400 bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors">
          <Pencil size={14} /> 編集
        </Link>
      </div>

      {/* タブ */}
      <div className="flex gap-1 bg-gray-900 rounded-lg p-1 mb-6 w-fit border border-gray-800">
        {(["backtest", "performance"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
            }`}>
            {t === "backtest" ? "バックテスト" : "現在の設定"}
          </button>
        ))}
      </div>

      {tab === "backtest" && (
        <div className="space-y-6">
          {/* 期間選択 + 実行 */}
          <div className="flex items-center gap-3">
            <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-lg p-1">
              {PERIODS.map((p) => (
                <button key={p.value} onClick={() => setPeriod(p.value)}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    period === p.value ? "bg-gray-700 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}>
                  {p.label}
                </button>
              ))}
            </div>
            <button onClick={handleBacktest} disabled={running}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              {running ? "実行中..." : "バックテスト実行"}
            </button>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          {result && (
            <div className="space-y-6">
              {/* サマリー */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard label="総損益"
                  value={`${result.total_pnl >= 0 ? "+" : ""}${result.total_pnl.toLocaleString()}円`}
                  positive={result.total_pnl >= 0} />
                <StatCard label="取引回数" value={`${result.trade_count}回`} />
                <StatCard label="勝率" value={`${result.win_rate.toFixed(1)}%`}
                  positive={result.win_rate >= 50} />
                <StatCard label="最大DD" value={`${result.max_drawdown.toFixed(1)}%`}
                  positive={result.max_drawdown < 10} />
              </div>

              {/* 資産推移グラフ */}
              {result.equity_curve.length > 0 && (
                <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                  <p className="text-sm font-medium text-gray-400 mb-4">資産推移</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <AreaChart data={result.equity_curve}>
                      <defs>
                        <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="timestamp"
                        tickFormatter={(ts) => new Date(ts).toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" })}
                        tick={{ fill: "#6b7280", fontSize: 11 }} />
                      <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                        tick={{ fill: "#6b7280", fontSize: 11 }} width={45} />
                      <Tooltip
                        formatter={(v) => [`${Number(v).toLocaleString()}円`, "資産"]}
                        labelFormatter={(ts) => new Date(ts).toLocaleString("ja-JP")}
                        contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                        labelStyle={{ color: "#9ca3af" }}
                      />
                      <Area type="monotone" dataKey="equity" stroke="#6366f1" fill="url(#equityGrad)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* 取引一覧 */}
              {result.trades.length > 0 && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                  <p className="text-sm font-medium text-gray-400 px-5 py-3 border-b border-gray-800">取引履歴</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-gray-500 text-xs border-b border-gray-800">
                          <th className="text-left px-5 py-2">日時</th>
                          <th className="text-left px-4 py-2">売買</th>
                          <th className="text-right px-4 py-2">価格</th>
                          <th className="text-right px-5 py-2">損益</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.trades.map((t, i) => (
                          <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/40">
                            <td className="px-5 py-2.5 text-gray-400 text-xs">
                              {new Date(t.timestamp).toLocaleString("ja-JP")}
                            </td>
                            <td className="px-4 py-2.5">
                              <span className={`flex items-center gap-1 font-medium ${t.side === "buy" ? "text-emerald-400" : "text-red-400"}`}>
                                {t.side === "buy" ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                                {t.side === "buy" ? "買" : "売"}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-right text-gray-300">
                              {t.price.toLocaleString()}円
                            </td>
                            <td className="px-5 py-2.5 text-right font-medium">
                              {t.pnl != null ? (
                                <span className={t.pnl >= 0 ? "text-emerald-400" : "text-red-400"}>
                                  {t.pnl >= 0 ? "+" : ""}{t.pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}円
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
              )}
            </div>
          )}

          {!result && !running && (
            <div className="text-center py-16 text-gray-600">
              <p>期間を選択して「バックテスト実行」をクリックしてください</p>
            </div>
          )}
        </div>
      )}

      {tab === "performance" && (
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-3 text-sm">
          <Row label="取引所" value={bot.exchange} />
          <Row label="通貨ペア" value={bot.symbol} />
          <Row label="トレード種別" value={bot.trade_type === "spot" ? "現物" : "先物"} />
          <Row label="戦略" value={bot.strategy.toUpperCase()} />
          <Row label="資金枠" value={`${bot.budget.toLocaleString()}円`} />
          <Row label="ストップロス" value={`${bot.stop_loss_pct}%`} />
          <Row label="タイムフレーム" value={String(params.timeframe ?? "1h")} />
          <Row label="実行間隔" value={`${params.interval_seconds ?? 3600}秒`} />
          {bot.strategy === "macd" && <>
            <Row label="MACD fast" value={String(params.fast ?? 12)} />
            <Row label="MACD slow" value={String(params.slow ?? 26)} />
            <Row label="MACD signal" value={String(params.signal ?? 9)} />
          </>}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${positive === true ? "text-emerald-400" : positive === false ? "text-red-400" : "text-white"}`}>
        {value}
      </p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200">{value}</span>
    </div>
  );
}
