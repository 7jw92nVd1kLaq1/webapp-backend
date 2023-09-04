const Xvfb = require("xvfb");
const fetchAmazonData = require("./util/amazon");
const {
  fetchCurrencyConversionData,
  fetchCryptoCurrencyPrice,
} = require("./util/currency");

const http = require("http");

const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
puppeteer.use(StealthPlugin());
const AdblockerPlugin = require("puppeteer-extra-plugin-adblocker");
puppeteer.use(AdblockerPlugin({ blockTrackers: true }));

const express = require("express");
const app = express();
app.use(express.json());
const port = 3000;

(async () => {
  const xvfb = new Xvfb({
    silent: true,
    xvfb_args: ["-screen", "0", "1280x720x24", "-ac"],
  });
  xvfb.start((err) => {
    if (err) console.error(err);
  });
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null, //otherwise it defaults to 800x600
    args: [
      "--no-sandbox",
      "--start-fullscreen",
      "--disable-setuid-sandbox",
      "--font-render-hinting=none",
      "--display=" + xvfb._display,
    ],
    executablePath: process.env.PUPPETEER_EXEC_PATH,
    env: { DISPLAY: ":0.0" },
  });

  // Express.js paths
  app.post("/", async (req, res) => {
    console.log("Request received!!!! Someone made a request");
    const data = await fetchAmazonData(browser, req.body.url);
    console.log(data);
    res.json(data);
  });

  app.get("/getCurrencyData/", async (req, res) => {
    const data = await fetchCurrencyConversionData(browser);
    res.json(data);
  });

  app.get("/getCurrencySymbols/", async (req, res) => {
    const data = await fetchFiatCurrencyData.fetchCurrencySymbols(browser);
    res.json(data);
  });

  app.post("/captchaImageSolve/", async (req, res) => {
    const url = req.body.url;
  });

  app.post("/getCryptoCurrencyData/", async (req, res) => {
    const name = req.body.name;
    const ticker = req.body.ticker;

    const data = await fetchCryptoCurrencyPrice(browser, name, ticker);
    res.json(data);
  });

  app.listen(port, () => {
    console.log(
      `Server running.... You can access the server at port ${port}.`
    );
  });
})();
