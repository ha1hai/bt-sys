"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { bots, type Bot } from "@/lib/api";
import { FieldWithTip } from "@/components/FieldWithTip";

const SYMBOLS = ["BTC/JPY", "ETH/JPY", "XRP/JPY"];
const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];
const STRATEGIES = [{ value: "macd", label: "MACD" }];

const MACD_TIPS = {
  fast: "短期EMAの計算期間。小さいほど直近の値動きに敏感に反応します。標準値は12。",
  slow: "長期EMAの計算期間。大きいほど長期トレンドを重視します。標準値は26。fast より大きい値を設定してください。",
  signal: "MACDラインをさらに平滑化する期間。MACDとシグナルのクロスで売買シグナルが発生します。標準値は9。",
};

type Form = {
  name: string;
  exchange: string;
  symbol: string;
  trade_type: string;
  strategy: string;
  budget: number;
  stop_loss_pct: number;
  interval_seconds: number;
  timeframe: string;
  fast: number;
  slow: number;
  signal: number;
};

function botToForm(bot: Bot): Form {
  const p = bot.strategy_params as Record<string, number | string>;
  return {
    name: bot.name,
    exchange: bot.exchange,
    symbol: bot.symbol,
    trade_type: bot.trade_type,
    strategy: bot.strategy,
    budget: bot.budget,
    stop_loss_pct: bot.stop_loss_pct,
    interval_seconds: (p.interval_seconds as number) ?? 3600,
    timeframe: (p.timeframe as string) ?? "1h",
    fast: (p.fast as number) ?? 12,
    slow: (p.slow as number) ?? 26,
    signal: (p.signal as number) ?? 9,
  };
}

export default function EditBotPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [form, setForm] = useState<Form | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    bots.get(id).then((bot) => {
      setForm(botToForm(bot));
      setIsRunning(bot.status === "running");
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  const set = (key: keyof Form, value: unknown) =>
    setForm((f) => f ? { ...f, [key]: value } : f);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setError("");
    setSaving(true);
    try {
      await bots.update(id, {
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
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-gray-400">読み込み中...</div>;
  if (!form) return <div className="p-8 text-red-400">{error || "ボットが見つかりません"}</div>;

  return (
    <div className="p-8 max-w-xl">
      <Link href="/dashboard" className="flex items-center gap-2 text-gray-400 hover:text-gray-200 text-sm mb-6">
        <ArrowLeft size={16} /> 戻る
      </Link>
      <h1 className="text-xl font-semibold mb-2">ボット設定の編集</h1>
      {isRunning && (
        <p className="text-amber-400 text-sm mb-6 bg-amber-500/10 rounded-lg px-3 py-2">
          稼働中のボットです。変更は次の実行サイクルから反映されます。
        </p>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 mt-6">
        {/* 基本設定 */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">基本設定</h2>
          <FieldWithTip label="ボット名">
            <input value={form.name} onChange={(e) => set("name", e.target.value)}
              required className="input" />
          </FieldWithTip>
          <FieldWithTip label="取引所" tip="取引を行う仮想通貨取引所。現在は bitFlyer のみ対応しています。">
            <select value={form.exchange} onChange={(e) => set("exchange", e.target.value)} className="input">
              <option value="bitflyer">bitFlyer</option>
            </select>
          </FieldWithTip>
          <FieldWithTip label="通貨ペア" tip="売買する通貨の組み合わせ。例：BTC/JPY は日本円でビットコインを売買します。">
            <select value={form.symbol} onChange={(e) => set("symbol", e.target.value)} className="input">
              {SYMBOLS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </FieldWithTip>
          <FieldWithTip label="トレード種別" tip="現物：実際の通貨を売買します。先物：将来の価格を予約する取引で、レバレッジをかけることができます。初心者には現物を推奨します。">
            <select value={form.trade_type} onChange={(e) => set("trade_type", e.target.value)} className="input">
              <option value="spot">現物</option>
              <option value="futures">先物</option>
            </select>
          </FieldWithTip>
        </section>

        {/* 資金・リスク */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">資金・リスク管理</h2>
          <FieldWithTip label="資金枠（円）" tip="このボットが1回の買い注文で使う上限金額。口座残高の範囲内で設定してください。例：10000円に設定するとBTC価格が500万円の場合、0.002BTC を購入します。">
            <input type="number" value={form.budget} onChange={(e) => set("budget", Number(e.target.value))}
              min={1} required className="input" />
          </FieldWithTip>
          <FieldWithTip label="ストップロス（%）" tip="保有中のポジションの含み損がこの割合を超えると自動的に売却します。例：5% に設定した場合、10000円で買ったポジションが9500円を下回ると損切りします。リスク管理のため必ず設定してください。">
            <input type="number" value={form.stop_loss_pct} onChange={(e) => set("stop_loss_pct", Number(e.target.value))}
              min={0.1} max={100} step={0.1} required className="input" />
          </FieldWithTip>
        </section>

        {/* 戦略・実行設定 */}
        <section className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">戦略・実行設定</h2>
          <FieldWithTip label="戦略" tip="売買シグナルを判断するアルゴリズム。MACD は移動平均線の差を使ったトレンドフォロー型の戦略です。">
            <select value={form.strategy} onChange={(e) => set("strategy", e.target.value)} className="input">
              {STRATEGIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </FieldWithTip>
          <FieldWithTip label="タイムフレーム" tip="売買判断に使うローソク足の時間単位。短いほど頻繁に取引しますが、手数料やノイズの影響を受けやすくなります。初心者には1時間足（1h）を推奨します。">
            <select value={form.timeframe} onChange={(e) => set("timeframe", e.target.value)} className="input">
              {TIMEFRAMES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </FieldWithTip>
          <FieldWithTip label="実行間隔（秒）" tip="ボットがシグナルを確認する頻度。タイムフレームと合わせて設定してください。例：1時間足なら3600秒（1時間）。短くしすぎても意味はありません。">
            <input type="number" value={form.interval_seconds} onChange={(e) => set("interval_seconds", Number(e.target.value))}
              min={60} step={60} required className="input" />
          </FieldWithTip>
          {form.strategy === "macd" && (
            <div className="grid grid-cols-3 gap-3">
              {(["fast", "slow", "signal"] as const).map((key) => (
                <FieldWithTip key={key} label={key} tip={MACD_TIPS[key]}>
                  <input type="number" value={form[key]} onChange={(e) => set(key, Number(e.target.value))}
                    min={2} required className="input" />
                </FieldWithTip>
              ))}
            </div>
          )}
        </section>

        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button type="submit" disabled={saving}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg py-2.5 text-sm font-medium transition-colors">
          {saving ? "保存中..." : "変更を保存"}
        </button>
      </form>
    </div>
  );
}

