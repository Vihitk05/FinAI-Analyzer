import { ArrowUpRight, TrendingUp } from "lucide-react";

export function ReportSummary({ company, date, revenue, ebitda, netIncome }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Company</p>
          <p className="font-medium">{company}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Analysis Date</p>
          <p className="font-medium">March 22, 2025</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Revenue</p>
          <div className="flex items-center">
            <p className="font-medium mr-1">{revenue}</p>
            <TrendingUp className="h-3 w-3 text-green-500" />
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">EBITDA</p>
          <div className="flex items-center">
            <p className="font-medium mr-1">{ebitda}</p>
            <TrendingUp className="h-3 w-3 text-green-500" />
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Net Income</p>
          <div className="flex items-center">
            <p className="font-medium mr-1">{netIncome}</p>
            <TrendingUp className="h-3 w-3 text-green-500" />
          </div>
        </div>
      </div>

      <div className="pt-2">
        <div className="flex items-center text-sm text-primary">
          <span className="mr-1">View key insights</span>
          <ArrowUpRight className="h-3 w-3" />
        </div>
      </div>
    </div>
  );
}