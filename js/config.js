/**
 * Cocktail Embassy — runtime configuration.
 *
 * apiBase: URL of the order/back-office API (the BotHost service in /server).
 *   Leave empty to run the site as a static catalogue on GitHub Pages.
 *   Example: "https://cocktail-embassy.bothost.ru"
 *
 * The site keeps working with bundled data (data/content.json) when the API
 * is unreachable, so GitHub Pages always renders a full catalogue.
 */
window.CE_CONFIG = {
  apiBase: "",
  telegramAdmin: "",
  requestEmail: "orders@cocktailembassy.com",
};
