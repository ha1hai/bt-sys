"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { bots } from "@/lib/api";

const STRATEGIES = [{ value: "macd", label: "MACD" }];
const SYMBOLS = ["BTC/JPY", "ETH/JPY", "XRP/JPY"];
const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

export default function NewBotPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    exchange: "bitflyer",
    symbol: "BTC/JPY",
    trade_type: "spot",
    strategy: "macd",
    budget: 10000,
    stop_loss_pct: 5,
    interval_seconds: 3600,
    timeframe: "1h",
    fast: 12,
    slow: 26,
    signal: 9,
  });

  const set = (key: string, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await bots.create({
        name: form.name,
        exchange: form.exchange,
        symbol: form.symbol,
        trade_type: form.trade_type,
        strategy: form.strategy,
        budget: form.budget,
        stop_loss_pct: form.stop_loss_pct,
        strategy_params: {
          interval_seconds: form.interval_seconds,
          timeframe: form.timeframe,
          fast: form.fast,
          slow: form.slow,
          signal: form.signal,
        },
      });
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-xl">
      <Link href="/dashboard" className="flex items-center gap-2 text-gray-400 hover:text-gray-200 text-sm mb-6">
        <ArrowLeft size={16} /> 戻る
      </Link>
      <h1 className="text-xl font-semibold mb-6">ボット作成</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本設定 */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">基本設定</h2>
          <Field label="ボット名">
            <input
              value={form.name} onChange={(e) => set("name", e.target.value)}
              required placeholder="例: BTC MACD Bot"
              className="input"
            />
          </Field>
          <Field label="取引所">
            <select value={form.exchange} onChange={(e) => set("exchange", e.target.value)} className="input">
              <option value="bitflyer">bitFlyer</option>
            </select>
          </Field>
          <Field label="通貨ペア">
            <select value={form.symbol} onChange={(e) => set("symbol", e.target.value)} className="input">
              {SYMBOLS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="トレード種別">
            <select value={form.trade_type} onChange={(e) => set("trade_type", e.target.value)} className="input">
              <option value="spot">現物</option>
              <option value="futures">先物</option>
            </select>
          </Field>
        </section>

        {/* 資金・リスク */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">資金・リスク管理</h2>
          <Field label="資金枠（円）">
            <input type="number" value={form.budget} onChange={(e) => set("budget", Number(e.target.value))}
              min={1} required className="input" />
          </Field>
          <Field label="ストップロス（%）">
            <input type="number" value={form.stop_loss_pct} onChange={(e) => set("stop_loss_pct", Number(e.target.value))}
              min={0.1} max={100} step={0.1} required className="input" />
          </Field>
        </section>

        {/* 戦略・実行設定 */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">戦略・実行設定</h2>
          <Field label="戦略">
            <select value={form.strategy} onChange={(e) => set("strategy", e.target.value)} className="input">
              {STRATEGIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </Field>
          <Field label="タイムフレーム">
            <select value={form.timeframe} onChange={(e) => set("timeframe", e.target.value)} className="input">
              {TIMEFRAMES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="実行間隔（秒）">
            <input type="number" value={form.interval_seconds} onChange={(e) => set("interval_seconds", Number(e.target.value))}
              min={60} step={60} required className="input" />
          </Field>
          {form.strategy === "macd" && (
            <div className="grid grid-cols-3 gap-3">
              {(["fast", "slow", "signal"] as const).map((key) => (
                <Field key={key} label={key}>
                  <input type="number" value={form[key]} onChange={(e) => set(key, Number(e.target.value))}
                    min={2} required className="input" />
                </Field>
              ))}
            </div>
          )}
        </section>

        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg py-2.5 text-sm font-medium transition-colors">
          {loading ? "作成中..." : "ボットを作成"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1 capitalize">{label}</label>
      {children}
    </div>
  );
}
