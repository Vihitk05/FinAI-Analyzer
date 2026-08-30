import { ArrowUpRight, TrendingUp } from "lucide-react";
import { formatMoneyCompact } from "@/lib/currency";

export function ReportSummary({ company, date, revenue, netIncome, currency }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Company</p>
          <p className="break-words font-medium">{company}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Analysis Date</p>
          <p className="break-words font-medium">{date}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="min-w-0 space-y-1">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Revenue</p>
          <div className="flex min-w-0 items-center">
            <p className="mr-1 min-w-0 break-words font-medium">{formatMoneyCompact(revenue, currency)}</p>
            <TrendingUp className="h-3 w-3 shrink-0 text-green-500" />
          </div>
        </div>
        <div className="min-w-0 space-y-1">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Net Income</p>
          <div className="flex min-w-0 items-center">
            <p className="mr-1 min-w-0 break-words font-medium">{formatMoneyCompact(netIncome, currency)}</p>
            <TrendingUp className="h-3 w-3 shrink-0 text-green-500" />
          </div>
        </div>
      </div>
    </div>
  );
}
