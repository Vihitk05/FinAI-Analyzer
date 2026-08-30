"use client";

import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoneyCompact } from "@/lib/currency";

const COLORS = ["#2563eb", "#059669", "#d97706"];

function label(value) {
  return String(value || "").replace(/([a-z0-9])([A-Z])/g, "$1 $2").replace(/^./, (v) => v.toUpperCase());
}

const RATING_SCALE = {
  fair: { width: 40, bar: "bg-amber-500" },
  good: { width: 60, bar: "bg-blue-500" },
  strong: { width: 80, bar: "bg-green-500" },
  excellent: { width: 100, bar: "bg-green-500" },
  low: { width: 20, bar: "bg-green-500" },
  "low-medium": { width: 40, bar: "bg-blue-500" },
  medium: { width: 60, bar: "bg-amber-500" },
  "medium-high": { width: 80, bar: "bg-amber-500" },
  high: { width: 100, bar: "bg-red-500" },
};

function isRatingValue(value) {
  return typeof value === "string" && RATING_SCALE[value.toLowerCase()] !== undefined;
}

function isCategoryAmountArray(value) {
  return Array.isArray(value) && value.length > 0 && value.every(
    (item) => item && typeof item === "object" && typeof item.category === "string" && typeof item.amount === "number"
  );
}

function isRatioArray(value) {
  return Array.isArray(value) && value.length > 0 && value.every(
    (item) => item && typeof item === "object" && typeof item.ratio === "string" && "value" in item
  );
}

function isPerfArray(value) {
  return Array.isArray(value) && value.length > 0 && value.every(
    (item) => item && typeof item === "object" && (typeof item.segment === "string" || typeof item.region === "string")
  );
}

function pct(v) {
  return v === null || v === undefined ? "-" : `${v > 0 ? "" : ""}${Number(v).toFixed(1)}%`;
}

function PerfTable({ items, currency }) {
  const unitKey = "segment" in items[0] ? "segment" : "region";
  const hasProfit = items.some((r) => r.operatingProfit !== undefined);
  return <div className="overflow-x-auto">
    <table className="w-full min-w-[32rem] text-sm">
      <thead><tr className="border-b text-left text-xs uppercase tracking-wide text-slate-500">
        <th className="py-1 pr-3">{unitKey}</th>
        <th className="py-1 pr-3 text-right">Revenue</th>
        <th className="py-1 pr-3 text-right">Growth</th>
        <th className="py-1 pr-3 text-right">% of revenue</th>
        {hasProfit ? <th className="py-1 pr-3 text-right">Op. profit</th> : null}
        {hasProfit ? <th className="py-1 pr-3 text-right">Margin</th> : null}
        {hasProfit ? <th className="py-1 text-right">% of profit</th> : null}
      </tr></thead>
      <tbody>
        {items.map((r, i) => <tr key={i} className="border-b border-slate-100">
          <td className="py-1.5 pr-3 font-medium text-slate-700">{r[unitKey]}</td>
          <td className="py-1.5 pr-3 text-right">{formatMoneyCompact(r.revenue, currency)}</td>
          <td className="py-1.5 pr-3 text-right">{r.revenueGrowth === null || r.revenueGrowth === undefined ? "-" : `${r.revenueGrowth > 0 ? "+" : ""}${Number(r.revenueGrowth).toFixed(1)}%`}</td>
          <td className="py-1.5 pr-3 text-right">{pct(r.contributionToRevenuePercent)}</td>
          {hasProfit ? <td className="py-1.5 pr-3 text-right">{r.operatingProfit === undefined ? "-" : formatMoneyCompact(r.operatingProfit, currency)}</td> : null}
          {hasProfit ? <td className="py-1.5 pr-3 text-right">{pct(r.marginPercent)}</td> : null}
          {hasProfit ? <td className="py-1.5 text-right">{pct(r.contributionToProfitPercent)}</td> : null}
        </tr>)}
      </tbody>
    </table>
  </div>;
}

function NotesDisclosures({ notes = [] }) {
  if (!notes.length) return null;
  return <section>
    <h2 className="mb-3 text-lg font-semibold uppercase tracking-wide text-blue-950">Notes &amp; Disclosures</h2>
    <div className="grid gap-4 xl:grid-cols-2">
      {notes.map((note) => <Card key={note.field} className="border-blue-100">
        <CardHeader className="pb-2"><div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{note.category}</CardTitle><StatusBadge status={note.status} />
        </div></CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1.5 break-words pl-5 text-sm text-slate-700">
            {note.items.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
          <Citation citations={note.citations} provenance={note.provenance} />
        </CardContent>
      </Card>)}
    </div>
  </section>;
}

const STATUS_BADGE = {
  verified: { label: "Verified source", cls: "bg-green-50 text-green-800 border-green-200" },
  calculated: { label: "Calculated", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  needs_review: { label: "Needs review", cls: "bg-amber-50 text-amber-900 border-amber-300" },
  conflicting: { label: "Conflicting sources", cls: "bg-red-50 text-red-800 border-red-300" },
  unavailable: { label: "Not identified", cls: "bg-slate-100 text-slate-600 border-slate-200" },
  not_applicable: { label: "Not applicable", cls: "bg-slate-100 text-slate-500 border-slate-200" },
};

function StatusBadge({ status }) {
  const badge = STATUS_BADGE[status];
  if (!badge) return null;
  return <span className={`inline-block whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium ${badge.cls}`}>{badge.label}</span>;
}

function SourceDetails({ provenance = [], citations = [] }) {
  const sources = provenance.length
    ? provenance
    : citations.map((c) => ({
        name: c.filename || "Uploaded report",
        document: c.filename || "Uploaded report",
        page: c.page,
        section: null,
        reportingPeriod: null,
        verified: c.verificationStatus === "verified",
        verificationMethod: "source_text_match",
        supports: c.description,
      }));
  if (!sources.length) return null;
  const first = sources[0];
  return <details className="mt-3 min-w-0 overflow-hidden border-l-2 border-blue-300 pl-3 text-xs text-blue-900">
    <summary className="cursor-pointer list-none font-semibold [overflow-wrap:anywhere]">
      {first.verified ? "Verified source" : "Source"} · {first.document || first.name}
      {first.page ? ` · p.${first.page}` : ""}
      {sources.length > 1 ? ` (+${sources.length - 1} more)` : ""}
      <span className="ml-2 whitespace-nowrap font-normal text-blue-600 underline">View source details</span>
    </summary>
    <div className="mt-2 space-y-3">
      {sources.map((s, index) => <dl key={`${s.document}-${s.page}-${index}`} className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-3 gap-y-1">
        <dt className="text-blue-500">Source</dt><dd className="min-w-0 font-medium [overflow-wrap:anywhere]">{s.name || s.document}</dd>
        {s.section && <><dt className="text-blue-500">Section</dt><dd className="min-w-0 [overflow-wrap:anywhere]">{s.section}</dd></>}
        {s.page != null && <><dt className="text-blue-500">Page</dt><dd className="min-w-0">{s.page}</dd></>}
        {s.reportingPeriod && <><dt className="text-blue-500">Reporting period</dt><dd className="min-w-0 [overflow-wrap:anywhere]">{s.reportingPeriod}</dd></>}
        {s.supports && <><dt className="text-blue-500">Supports</dt><dd className="min-w-0 [overflow-wrap:anywhere]">{s.supports}</dd></>}
        <dt className="text-blue-500">Verification</dt>
        <dd className="min-w-0 [overflow-wrap:anywhere]">{s.verified ? "✓ Source text matched" : "Unverified"}{s.verificationMethod ? ` (${s.verificationMethod.replace(/_/g, " ")})` : ""}</dd>
      </dl>)}
    </div>
  </details>;
}

function Citation({ citations = [], provenance = [] }) {
  return <SourceDetails citations={citations} provenance={provenance} />;
}

function FallbackNote({ fact }) {
  if (!fact?.isFallbackSource) return null;
  return <p className="mt-2 break-words text-xs italic text-amber-700">Not reported in the latest source; shown from an earlier report ({fact.sourcedFromPeriod}).</p>;
}

function FormatMetric({ value, field, currency }) {
  if (typeof value !== "number") return String(value);
  if (field?.toLowerCase().includes("change") || field?.toLowerCase().includes("margin")) return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
  return formatMoneyCompact(value, currency);
}

function RatingBar({ value }) {
  const scale = RATING_SCALE[value.toLowerCase()] || { width: 0, bar: "bg-blue-500" };
  return <div className="flex items-center gap-3">
    <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-blue-100"><div className={`h-full ${scale.bar}`} style={{ width: `${scale.width}%` }} /></div>
    <span className="text-sm font-medium text-slate-800">{value}</span>
  </div>;
}

function RatioList({ items }) {
  const rows = items.filter((item) => item.value !== null && item.value !== undefined && item.value !== "");
  if (!rows.length) return null;
  return <ul className="divide-y divide-blue-50">
    {rows.map((item, index) => <li key={index} className="flex items-center justify-between py-2 text-sm">
      <span className="uppercase tracking-wide text-slate-700">{item.ratio}</span>
      <span className="font-medium text-blue-900">{typeof item.value === "number" ? (item.isPercentage ? `${item.value.toFixed(1)}%` : item.value.toLocaleString()) : String(item.value)}</span>
    </li>)}
  </ul>;
}

const truncateLabel = (value, max = 20) => (value.length > max ? `${value.slice(0, max - 1)}…` : value);

function CategoryTick({ x, y, payload }) {
  return <text x={x} y={y} dy={4} textAnchor="end" fontSize={10} fill="#475569">{truncateLabel(payload.value)}</text>;
}

function CategoryBreakdown({ items, currency }) {
  const data = [...items].sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount)).slice(0, 10);
  if (data.length < 2) {
    const item = data[0];
    return item ? <p className="text-sm text-slate-700">{item.category}: <span className="font-medium">{formatMoneyCompact(item.amount, currency)}</span></p> : null;
  }
  return <div style={{ height: Math.max(140, data.length * 44) }}>
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tickFormatter={(v) => formatMoneyCompact(v, currency)} tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey="category" width={132} tick={<CategoryTick />} interval={0} />
        <Tooltip formatter={(v) => formatMoneyCompact(v, currency)} labelFormatter={(value) => value} />
        <Bar dataKey="amount" fill={COLORS[0]} radius={[0, 4, 4, 0]} barSize={22} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  </div>;
}

function Fact({ fact, currency }) {
  let content;
  if (isRatingValue(fact.value)) {
    content = <RatingBar value={fact.value} />;
  } else if (isPerfArray(fact.value)) {
    content = <PerfTable items={fact.value} currency={currency} />;
  } else if (isRatioArray(fact.value)) {
    content = <RatioList items={fact.value} />;
  } else if (isCategoryAmountArray(fact.value)) {
    content = <CategoryBreakdown items={fact.value} currency={currency} />;
  } else if (Array.isArray(fact.value)) {
    const items = fact.value.filter(Boolean);
    content = items.length ? <ul className="list-disc space-y-2 break-words pl-5 text-sm text-slate-700">{items.map((item, i) => <li key={i}>{typeof item === "string" ? item : JSON.stringify(item)}</li>)}</ul> : null;
  } else if (fact.value && typeof fact.value === "object") {
    const entries = Object.entries(fact.value).filter(([, v]) => v !== null && v !== undefined && v !== "");
    content = entries.length ? <dl className="space-y-1 text-sm">{entries.map(([k, v]) => <div key={k} className="flex flex-wrap justify-between gap-x-4 gap-y-1"><dt className="shrink-0 uppercase tracking-wide text-slate-500">{label(k)}</dt><dd className="min-w-0 break-words text-right font-medium text-slate-800">{String(v)}</dd></div>)}</dl> : null;
  } else {
    content = <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{String(fact.value)}</p>;
  }
  if (!content) return null;
  return <Card className="border-blue-100"><CardHeader className="pb-2"><div className="flex items-start justify-between gap-2"><CardTitle className="text-base">{label(fact.field)}</CardTitle><StatusBadge status={fact.status} /></div></CardHeader><CardContent>{content}<FallbackNote fact={fact} /><Citation citations={fact.citations} provenance={fact.provenance} /></CardContent></Card>;
}

function Chart({ chart, currency }) {
  const tick = (value) => formatMoneyCompact(value, currency);
  return <Card className="border-blue-100"><CardHeader className="pb-2"><CardTitle className="text-base">{chart.title}</CardTitle><CardDescription>Reported values by source period ({currency || "reported currency"})</CardDescription></CardHeader><CardContent className="h-80 pt-4">
    <ResponsiveContainer width="100%" height="100%"><LineChart data={chart.data} margin={{ top: 8, right: 28, left: 28, bottom: 48 }}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="period" interval={0} angle={-18} textAnchor="end" height={62} tick={{ fontSize: 11 }} /><YAxis width={84} tickFormatter={tick} tick={{ fontSize: 11 }} /><Tooltip formatter={(value) => [formatMoneyCompact(value, currency), chart.title]} labelFormatter={(period) => `Period: ${period}`} /><Legend /><Line type="linear" dataKey="value" name={chart.title} stroke={COLORS[0]} strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} /></LineChart></ResponsiveContainer>
  </CardContent></Card>;
}

const SUMMARY_FIELDS = ["executiveSummary", "businessOverviewSummary", "companyProfile"];

function pickSummaryFact(facts = []) {
  for (const field of SUMMARY_FIELDS) {
    const fact = facts.find((f) => f.field === field && typeof f.value === "string" && f.value.trim());
    if (fact) return fact;
  }
  return null;
}

function DocumentsAnalyzed({ data }) {
  const reports = data.sourceReports || [];
  if (!reports.length) return null;
  return <Card className="border-blue-200 bg-slate-50">
    <CardContent className="py-4">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-950">
        Documents analyzed: {reports.length}
      </p>
      <ul className="mt-2 space-y-1 text-sm text-slate-700">
        {reports.map((r) => <li key={r.id || r.filename} className="break-words">
          &bull; {r.period && r.period !== "Undated report" ? `${r.period}: ` : ""}{r.filename}
          {r.documentType ? <span className="text-slate-400"> ({label(r.documentType)})</span> : null}
        </li>)}
      </ul>
      {data.reportingPeriod && data.reportingPeriod !== "Undated report"
        ? <p className="mt-2 text-xs text-slate-500">Reporting period: {data.reportingPeriod}</p> : null}
    </CardContent>
  </Card>;
}

function ConflictBanner({ conflicts = [] }) {
  const unresolved = conflicts.filter((c) => c.status === "conflicting");
  if (!unresolved.length) return null;
  return <div role="alert" className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
    <p className="font-semibold">Source conflict{unresolved.length > 1 ? "s" : ""} detected</p>
    <ul className="mt-1 list-disc space-y-0.5 pl-5">
      {unresolved.map((c) => <li key={c.field}>
        {label(c.field)}: sources disagree by ~{c.spreadPercent}% for the same period, shown as unresolved rather than picking one.
      </li>)}
    </ul>
  </div>;
}

function MissingExpected({ items = [] }) {
  if (!items.length) return null;
  return <Card className="border-slate-200">
    <CardHeader className="pb-2"><CardTitle className="text-base text-slate-600">Not identified in the verified sources</CardTitle></CardHeader>
    <CardContent>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
        {items.map((m) => <li key={m.field}>{m.message}</li>)}
      </ul>
    </CardContent>
  </Card>;
}

export function CuratedDashboard({ data }) {
  if (!data) return null;
  const summaryFact = pickSummaryFact(data.facts);
  const remainingFacts = summaryFact ? data.facts.filter((f) => f.field !== summaryFact.field) : data.facts;
  return <div className="space-y-6">
    {data.isDemo && <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">{data.demoNotice}</div>}
    {data.currencyMismatch && <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">Reports in different currencies are not combined; charts use only the dominant compatible currency.</div>}
    <ConflictBanner conflicts={data.conflicts} />
    <DocumentsAnalyzed data={data} />
    {summaryFact && <Card className="border-blue-200 bg-blue-50/40"><CardHeader className="pb-2"><CardTitle className="text-base">Financial Summary</CardTitle></CardHeader><CardContent><p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-800">{summaryFact.value}</p><Citation citations={summaryFact.citations} provenance={summaryFact.provenance} /></CardContent></Card>}
    {data.metrics?.length > 0 && <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{data.metrics.map((metric) => <Card key={metric.field} className="border-blue-100"><CardHeader className="pb-2"><div className="flex items-start justify-between gap-2"><CardTitle className="text-sm font-medium">{metric.label || label(metric.field)}</CardTitle><StatusBadge status={metric.status} /></div></CardHeader><CardContent><p className="text-2xl font-bold text-blue-800"><FormatMetric value={metric.value} field={metric.field} currency={data.currency} /></p><FallbackNote fact={metric} /><Citation citations={metric.citations} provenance={metric.provenance} /></CardContent></Card>)}</section>}
    {data.charts?.length > 0 && <section className="grid gap-6 xl:grid-cols-2">{data.charts.map((chart) => <Chart key={chart.field} chart={chart} currency={data.currency} />)}</section>}
    {data.derivedMetrics?.length > 0 && <section className="grid gap-4 md:grid-cols-2">{data.derivedMetrics.map((metric) => <Card key={metric.field} className="border-blue-100"><CardHeader className="pb-2"><div className="flex items-start justify-between gap-2"><CardTitle className="text-base">{metric.label}</CardTitle><StatusBadge status={metric.status} /></div></CardHeader><CardContent><p className="text-2xl font-bold text-blue-800"><FormatMetric value={metric.value} field={metric.field} currency={data.currency} /></p><p className="mt-2 text-xs text-slate-600">Calculated deterministically: {metric.formula}</p><Citation citations={metric.citations} provenance={metric.provenance} /></CardContent></Card>)}</section>}
    {data.insights?.length > 0 && <section className="grid gap-4 xl:grid-cols-2">{data.insights.map((insight, index) => <Card key={`${insight.title}-${index}`} className="border-blue-100"><CardHeader className="pb-2"><CardTitle className="text-base">{insight.title}</CardTitle><CardDescription>{label(insight.kind)}</CardDescription></CardHeader><CardContent><p className="text-sm leading-6 text-slate-700">{insight.statement}</p><p className="mt-2 text-sm text-slate-600"><span className="font-medium">Why it matters:</span> {insight.why}</p><Citation citations={insight.citations} provenance={insight.provenance} /></CardContent></Card>)}</section>}
    {remainingFacts?.length > 0 && <section className="grid gap-6 xl:grid-cols-2">{remainingFacts.map((fact) => <Fact key={fact.field} fact={fact} currency={data.currency} />)}</section>}
    <NotesDisclosures notes={data.notesDisclosures} />
    <MissingExpected items={data.missingExpected} />
    {data.externalSources && data.externalSources.externalVerifiedSourceAvailable === false
      ? <p className="text-xs text-slate-400">{data.externalSources.message}</p> : null}
    {!data.metrics?.length && !data.facts?.length && !data.insights?.length && !data.notesDisclosures?.length && <Card><CardContent className="py-10 text-center text-sm text-muted-foreground">No verified dashboard facts are available yet. Unsupported fields are intentionally omitted.</CardContent></Card>}
  </div>;
}
