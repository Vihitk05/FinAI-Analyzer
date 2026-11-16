const CURRENCY_SYMBOLS = {
  USD: "$",
  EUR: "€",
  GBP: "£",
  INR: "₹",
  JPY: "¥",
  AED: "AED ",
  AUD: "A$",
  CAD: "C$",
};

export function currencySymbol(currencyCode) {
  if (!currencyCode) return "$";
  return CURRENCY_SYMBOLS[currencyCode.toUpperCase()] || `${currencyCode.toUpperCase()} `;
}

export function formatMoney(value, currencyCode) {
  if (typeof value !== "number" || isNaN(value)) return `${currencySymbol(currencyCode)}0`;
  return `${currencySymbol(currencyCode)}${value.toLocaleString()}`;
}

export function formatMoneyCompact(value, currencyCode) {
  if (typeof value !== "number" || isNaN(value)) return `${currencySymbol(currencyCode)}0`;
  const symbol = currencySymbol(currencyCode);
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${symbol}${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${symbol}${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${symbol}${(value / 1_000).toFixed(1)}K`;
  return `${symbol}${value}`;
}
