import React from "react";

export const FinancialRatiosTable = ({ data = [] }) => {
  // If no data is provided, use placeholder data
  const ratios =
    data && data.length > 0
      ? data
      : [
          { ratio: "Current Ratio", value: 1.2 },
          { ratio: "Debt-to-Equity", value: 0.8 },
          { ratio: "Operating Margin", value: 15.3 },
          { ratio: "Net Margin", value: 7.8 },
          { ratio: "Return on Assets", value: 9.2 },
          { ratio: "Return on Equity", value: 18.5 },
        ];

  // Function to get appropriate color based on the ratio type and value
  const getRatioColor = (ratio, value) => {
    if (!ratio) return "text-blue-600"; // Default color if ratio is undefined

    const lowerCaseRatio = ratio.toLowerCase(); // Safely convert to lowercase

    if (lowerCaseRatio.includes("margin") || lowerCaseRatio.includes("return")) {
      // For profitability ratios, higher is better
      if (value > 15) return "text-green-600";
      if (value > 8) return "text-blue-600";
      return "text-amber-600";
    } else if (lowerCaseRatio.includes("debt")) {
      // For debt ratios, lower is better
      if (value < 1) return "text-green-600";
      if (value < 2) return "text-blue-600";
      return "text-amber-600";
    } else if (lowerCaseRatio.includes("current")) {
      // For liquidity ratios like current ratio
      if (value > 1.5) return "text-green-600";
      if (value > 1) return "text-blue-600";
      return "text-amber-600";
    }

    // Default return
    return "text-blue-600";
  };

  // Format the value as a percentage if appropriate
  const formatValue = (ratio, value) => {
    if (!ratio || typeof value !== "number") return value; // Return value as is if ratio is undefined or value is not a number

    const lowerCaseRatio = ratio.toLowerCase(); // Safely convert to lowercase

    if (
      lowerCaseRatio.includes("margin") ||
      lowerCaseRatio.includes("return") ||
      lowerCaseRatio.includes("growth")
    ) {
      return `${value.toFixed(1)}%`;
    }

    return value.toFixed(2);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-3 px-2 font-medium text-muted-foreground">
              Ratio
            </th>
            <th className="text-right py-3 px-2 font-medium text-muted-foreground">
              Value
            </th>
          </tr>
        </thead>
        <tbody>
          {ratios.map((item, index) => (
            <tr key={index} className="border-b">
              <td className="py-3 px-2 text-muted-foreground">
                {item.ratio || "N/A"} {/* Display "N/A" if ratio is undefined */}
              </td>
              <td
                className={`py-3 px-2 text-right font-medium ${getRatioColor(item.ratio, item.value)}`}
              >
                {formatValue(item.ratio, item.value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};