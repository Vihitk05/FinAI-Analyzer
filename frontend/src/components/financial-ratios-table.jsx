import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function FinancialRatiosTable() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ratio</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Industry Avg</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">Current Ratio</TableCell>
          <TableCell>2.3</TableCell>
          <TableCell>1.8</TableCell>
          <TableCell>
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Good
            </span>
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Debt-to-Equity</TableCell>
          <TableCell>0.65</TableCell>
          <TableCell>0.5</TableCell>
          <TableCell>
            <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
              Average
            </span>
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Gross Margin</TableCell>
          <TableCell>42.8%</TableCell>
          <TableCell>38.5%</TableCell>
          <TableCell>
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Good
            </span>
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">ROA</TableCell>
          <TableCell>12.5%</TableCell>
          <TableCell>10.2%</TableCell>
          <TableCell>
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Good
            </span>
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Inventory Turnover</TableCell>
          <TableCell>5.2</TableCell>
          <TableCell>6.8</TableCell>
          <TableCell>
            <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
              Poor
            </span>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}