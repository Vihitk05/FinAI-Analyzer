import React from "react";

// Utility function to parse your financial ratios array
const parseFinancialRatios = (ratiosArray) => {
  if (!ratiosArray || !Array.isArray(ratiosArray)) return [];

  return ratiosArray.map(ratio => {
    // Handle cases where ratio might be an object or string
    let ratioString = typeof ratio === 'string' ? ratio : 
                     ratio?.ratio ? ratio.ratio : 
                     ratio?.name ? ratio.name : 
                     JSON.stringify(ratio);
    
    // Example string: "Current Ratio: 1.54 (2024)"
    const [namePart, valuePart] = ratioString.split(':');
    const ratioName = namePart?.trim() || "Unknown Ratio";
    
    // Extract the numeric value (might include percentage or 'x')
    let numericValue = 0;
    let isPercentage = false;
    
    if (valuePart) {
      const numericValueMatch = valuePart.match(/([\d.]+)/);
      numericValue = numericValueMatch ? parseFloat(numericValueMatch[1]) : 0;
      isPercentage = valuePart.includes('%');
    } else if (typeof ratio === 'object' && ratio.value !== undefined) {
      numericValue = ratio.value;
      isPercentage = ratio.isPercentage || false;
    }
    
    return {
      ratio: ratioName,
      value: isPercentage ? numericValue : numericValue,
      isPercentage: isPercentage
    };
  });
};

export const FinancialRatiosTable = ({ data = [] }) => {
  // Parse the input data if it's in string format or object format
  const parsedData = Array.isArray(data) ? parseFinancialRatios(data) : [];
  
  // If no data is provided, use placeholder data
  const ratios = parsedData.length > 0 ? parsedData : [
    { ratio: "Current Ratio", value: 1.2 },
    { ratio: "Debt-to-Equity", value: 0.8 },
    { ratio: "Operating Margin", value: 15.3, isPercentage: true },
    { ratio: "Net Margin", value: 7.8, isPercentage: true },
    { ratio: "Return on Assets", value: 9.2, isPercentage: true },
    { ratio: "Return on Equity", value: 18.5, isPercentage: true },
  ];

  // Function to get appropriate color based on the ratio type and value
  const getRatioColor = (ratio, value) => {
    if (!ratio) return "text-blue-600";

    const lowerCaseRatio = ratio.toLowerCase();

    if (lowerCaseRatio.includes("margin") || lowerCaseRatio.includes("return")) {
      if (value > 15) return "text-green-600";
      if (value > 8) return "text-blue-600";
      return "text-amber-600";
    } else if (lowerCaseRatio.includes("debt")) {
      if (value < 1) return "text-green-600";
      if (value < 2) return "text-blue-600";
      return "text-amber-600";
    } else if (lowerCaseRatio.includes("current")) {
      if (value > 1.5) return "text-green-600";
      if (value > 1) return "text-blue-600";
      return "text-amber-600";
    } else if (lowerCaseRatio.includes("turnover")) {
      if (value > 5) return "text-green-600";
      if (value > 3) return "text-blue-600";
      return "text-amber-600";
    }

    return "text-blue-600";
  };

  const formatValue = (ratio, value, isPercentage) => {
    if (typeof value !== "number") return value;

    const lowerCaseRatio = ratio?.toLowerCase() || "";

    if (isPercentage || 
        lowerCaseRatio.includes("margin") ||
        lowerCaseRatio.includes("return") ||
        lowerCaseRatio.includes("equity") ||
        lowerCaseRatio.includes("roe") ||
        lowerCaseRatio.includes("roa")) {
      return `${value.toFixed(1)}%`;
    }

    if (lowerCaseRatio.includes("turnover")) {
      return `${value.toFixed(2)}x`;
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
                {item.ratio || "N/A"}
              </td>
              <td
                className={`py-3 px-2 text-right font-medium ${getRatioColor(item.ratio, item.value)}`}
              >
                {formatValue(item.ratio, item.value, item.isPercentage)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};