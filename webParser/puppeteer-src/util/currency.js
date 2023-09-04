async function fetchCurrencyConversionData(browser) {
  const page = await browser.newPage();
  await page.goto("https://www.x-rates.com/table/?from=USD&amount=1");

  await page.waitForSelector("table.tablesorter.ratesTable");
  try {
    const fiatCurrenciesData = await page.$eval(
      "table.tablesorter.ratesTable",
      (table) => {
        const currenciesData = [];
        const currencyRows = table.lastElementChild.children;
        for (const currency of currencyRows) {
          const currencyObj = {};

          const url = new URL(currency.querySelector("a").getAttribute("href"));
          const searchParams = new URLSearchParams(url.search);

          currencyObj.ticker = searchParams.get("to");
          currencyObj.name = currency.firstElementChild.textContent;
          currencyObj.rateAgainstDollar =
            currency.children[1].firstElementChild.textContent;

          currenciesData.push(currencyObj);
        }
        return currenciesData;
      }
    );

    await page.close();
    return fiatCurrenciesData;
  } catch (err) {
    await page.close();
    return [];
  }
}

async function fetchCurrencySymbols(browser) {
  const page = await browser.newPage();
  await page.goto(
    "https://www.eurochange.co.uk/travel/tips/world-currency-abbreviations-symbols-and-codes-travel-money"
  );

  await page.waitForSelector("table");
  try {
    const symbols = await page.$eval("table", (table) => {
      const data = [];
      const currencies = table.lastElementChild.children;

      for (const currency of currencies) {
        const ticker = currency.children[1].textContent;
        const symbol = currency.lastElementChild.textContent;
        data.push({ [ticker]: symbol });
      }
      return data;
    });
    return symbols;
  } catch (err) {
    return [];
  }
}

async function fetchCryptoCurrencyPrice(browser, name, ticker) {
  const page = await browser.newPage();
  await page.goto(`https://www.livecoinwatch.com/price/${name}-${ticker}`);

  await page.waitForSelector("div.official-name");
  try {
    const rate = await page.$eval("div.official-name span.price", (price) =>
      price.textContent.slice(1)
    );

    await page.close();
    return { rate: rate };
  } catch (err) {
    await page.close();
    return { rate: "undefined" };
  }
}

module.exports = {
  fetchCurrencyConversionData: fetchCurrencyConversionData,
  fetchCurrencySymbols: fetchCurrencySymbols,
  fetchCryptoCurrencyPrice: fetchCryptoCurrencyPrice,
};
