const CURRENCY_SYMBOLS = {
  EUR: '€',
  USD: '$',
  GBP: '£',
  CHF: 'CHF',
  JPY: '¥',
  SEK: 'kr',
  NOK: 'kr',
  DKK: 'kr',
  PLN: 'zł',
  CZK: 'Kč',
  HUF: 'Ft',
  CAD: 'CA$',
  AUD: 'A$',
  MXN: 'MX$',
  BRL: 'R$',
};

export const getCurrencySymbol = (code) => CURRENCY_SYMBOLS[code] || code || '€';

export const formatAmount = (amount, currency) => {
  const symbol = getCurrencySymbol(currency);
  const value = typeof amount === 'number' ? amount.toFixed(2) : '0.00';
  return `${value}${symbol}`;
};
