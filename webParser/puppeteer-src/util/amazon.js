const axios = require("axios");

async function fetchAmazonData(browser, url) {
  const data = {};
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(url);

  try {
    const captcha = await solveCaptcha(page);
    if (captcha === false) return data;
    else if (captcha === null) console.log("This page is captcha-free.");
  } catch (err) {
    console.log(err);
  }

  console.log(`Page Accessed: ${url}`);
  try {
    const productName = await page.$eval(
      "span#productTitle",
      (title) => title.textContent
    );
    data.productName = productName.trim();
  } catch (err) {
    data.productName = "undefined";
  }

  try {
    const price = await page.$eval(
      ".a-price .a-offscreen",
      (price) => price.textContent
    );
    data.price = price.trim();
  } catch (err) {
    data.price = "undefined";
  }

  try {
    const imageurl = await page.$eval("img#landingImage", (image) => image.src);
    data.imageurl = imageurl;
  } catch (err) {
    try {
      const imageurl = await page.$eval(
        "div#unrolledImgNo0 > div > img",
        (image) => image.src
      );
      data.imageurl = imageurl;
    } catch (err) {
      data.imageurl = "undefined";
    }
  }

  try {
    const rating = await page.$eval(
      "#averageCustomerReviews a span",
      (review) => review.textContent
    );
    data.rating = rating.trim();
  } catch (err) {
    data.rating = "undefined";
  }

  try {
    const brand = await page.$eval(
      "a#bylineInfo",
      (brand) => brand.textContent
    );
    data.brand = brand.trim();
  } catch (err) {
    data.brand = "undefined";
  }

  domainRegex = new RegExp(
    "^(https://)?(www.)?amazon.(com.tr)?(com.au)?(com.br)?(com)?(co.uk)?(co.jp)?(ae)?(de)?(fr)?(es)?(in)?(nl)?(pl)?(se)?(sg)?(eg)?/"
  );
  webSiteDomain = await page.url();
  data.domain = webSiteDomain.match(domainRegex)[0];
  data.options = await fetchAmazonDataOptions(page);

  await page.close();
  return data;
}

const fetchAmazonDataOptions = async (page) => {
  const data = [];
  const options_candidate = await page.$$("form#twister > div");
  for (const candidate of options_candidate) {
    const hasDropMenu = await candidate.$(
      'select[name="dropdown_selected_size_name"]'
    );
    if (hasDropMenu) {
      const url = await page.url();
      const options = await parseDropDownOptions(candidate, url);
      if (options.length > 1) data.push(options);
    } else {
      const options = await parseClickOptions(candidate);
      if (options.length > 1) data.push(options);
    }
  }

  return data;
};

const parseDropDownOptions = async (elemHandle, url) => {
  const options = await elemHandle.$eval(
    'select[name="dropdown_selected_size_name"]',
    (elem, url) => {
      const urlRegex = /(?<=\d+\,)[\w]+/g;
      const result = [];
      result.push(elem.getAttribute("data-a-touch-header").replace(":", ""));
      const choices = elem.children;

      for (const choice of choices) {
        obj = {};
        if (choice === choices.item(0)) continue;
        obj.name = choice.textContent.trim();
        obj.url = choice.getAttribute("value").match(urlRegex)[0];
        obj.available = choice.classList.contains("dropdownAvailable")
          ? true
          : false;
        if (url.includes(obj.url) && obj.available) {
          obj.selectedOption = true;
        }
        result.push(obj);
      }

      return result;
    },
    url
  );

  return options;
};

const parseClickOptions = async (elemHandle) => {
  try {
    const options = await elemHandle.$eval("ul", (elem) => {
      const result = [];
      const choices = elem.children;

      for (const choice of choices) {
        url = choice.getAttribute("data-defaultasin");

        obj = {};
        obj.name = choice.title.replace("Click to select ", "");
        obj.url = choice.getAttribute("data-dp-url") ? url : "";
        obj.available = choice.classList.contains("swatchUnavailable")
          ? false
          : true;
        if (!obj.url && obj.available) {
          obj.selectedOption = true;
        }
        result.push(obj);
      }

      return result;
    });

    const label = await elemHandle.$eval(".a-row", (elem) => {
      return elem.firstElementChild.textContent;
    });

    options.unshift(label.trim().replace(":", ""));
    return options;
  } catch (err) {
    return [];
  }
};

function getBase64(url) {
  return axios
    .get(url, { responseType: "arraybuffer" })
    .then((response) =>
      Buffer.from(response.data, "binary").toString("base64")
    );
}

const solveCaptcha = async (page) => {
  const isCaptcha = await page.$("input#captchacharacters");
  if (!isCaptcha) return null;
  console.log("It is captcha!!!!!!");

  await page.waitForSelector("img");
  const url = await page.$eval("img", (elem) => elem.src);

  const img_b64 = await getBase64(url);
  const { data } = await axios.post(
    "http://host.docker.internal:7777/solve",
    { captcha: img_b64 },
    { headers: { "Content-Type": "application/json" } }
  );
  if (data.output.length != 6) return false;

  console.log(`Extracted: ${data.output}`);
  const val = await page.$eval(
    "input#captchacharacters",
    (elem, value) => {
      elem.value = value;
      return elem.value;
    },
    data.output
  );
  await page.click("button.a-button-text");
  const isCaptchaAgain = await page.$("input#captchacharacters");
  if (!isCaptchaAgain) console.log("Captcha beaten!!!!!!!!!");
  return true;
};

module.exports = fetchAmazonData;
