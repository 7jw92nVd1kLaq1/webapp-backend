const axios = require("axios");
const fs = require("fs");

const saveText = (fileName, content) => {
  fs.writeFile(`/parserFolder/${fileName}`, `${content}`, function (err) {
    if (err) {
      return console.log(err);
    }
    console.log("The file was saved!!");
  });
};

async function fetchAmazonData(browser, url) {
  const data = {};
  const page = await browser.newPage();
  await page.setRequestInterception(true);

  // if the page makes a  request to a resource type of image then abort that request
  // The purpose of this is to optimize the speed of Puppeteer by aborting all the requests for any image and CSS resources
  page.on("request", (request) => {
    if (
      request.resourceType() === "image" ||
      request.resourceType() === "stylesheet"
    )
      request.abort();
    else request.continue();
  });

  // Set the size of the viewport of the browser and proceed to a URL provided by a client
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(url, { waitUntil: "load" });

  // Amazon may deploy the captcha page to solve, then we request an external server for help for solving captcha
  try {
    const captcha = await solveCaptcha(page);
    if (captcha === false) return data;
    else if (captcha === null) console.log("This page is captcha-freee.");
  } catch (err) {
    console.log(err);
  }

  // Parse the name of the product
  try {
    const productName = await page.$eval(
      "span#productTitle",
      (title) => title.textContent
    );
    data.productName = productName.trim();
  } catch (err) {
    data.productName = "undefined";
  }

  // Parase the price of the product
  try {
    const price = await page.$eval(
      ".a-price .a-offscreen",
      (price) => price.textContent
    );
    data.price = price.trim();
  } catch (err) {
    data.price = "undefined";
  }

  // Parse the url of the image of the product
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

  // Parse the average rating of the product
  try {
    const rating = await page.$eval(
      "#averageCustomerReviews a span",
      (review) => review.textContent
    );
    data.rating = rating.trim();
  } catch (err) {
    data.rating = "undefined";
  }

  // Parse the brand of the product
  try {
    const brand = await page.$eval(
      "a#bylineInfo",
      (brand) => brand.textContent
    );
    data.brand = brand.trim();
  } catch (err) {
    data.brand = "undefined";
  }

  const domainRegex = new RegExp(
    "^(https://)?(www.)?amazon.(com.tr)?(com.au)?(com.br)?(com)?(co.uk)?(co.jp)?(ae)?(de)?(fr)?(es)?(in)?(nl)?(pl)?(se)?(sg)?(eg)?/"
  );
  const webSiteDomain = await page.url();
  data.domain = webSiteDomain.match(domainRegex)[0];

  data.options = await fetchAmazonDataOptions(page);

  await page.close();
  return data;
}

const fetchAmazonDataOptionsNew = async (page) => {
  console.log("NEW FUNCTION INVOKED");
  const expandOptionElements = await page.$$('[aria-label^="See"]');
  for (const elem of expandOptionElements) {
    try {
      await page.evaluate((elem) => elem.click(), elem);
    } catch (e) {
      console.log("FIRST");
      console.log(e);
    }
  }
  try {
    await page.waitForSelector("#desktop-configurator-side-sheet > ul", {
      timeout: 500,
    });
    const elems = await page.$$("#desktop-configurator-side-sheet > ul");
    console.log(elems.length);
  } catch (e) {
    console.log("SECOND");
    console.log(e);
  }

  const options = await page.$$eval(
    "#twister-plus-inline-twister > div",
    (elems) => {
      const options = {};
      for (const elem of elems) {
        let key;
        try {
          const elementWithKey = elem.querySelector(
            "div.a-section.inline-twister-dim-title-value-truncate-expanded > span.a-color-secondary"
          );
          key = elementWithKey.textContent.trim().slice(0, -1);
          options[key] = [];
        } catch (e) {
          console.log(e);
          options["hm"] = [];
          key = "hm";
        }

        const optionList = elem.querySelectorAll(
          "ul.a-button-list > li[data-asin], li.dimension-value-list-item-square-image"
        );
        for (const option of optionList) {
          const parsedOption = {};
          const url = option.getAttribute("data-asin");
          if (url) parsedOption.url = url;

          try {
            const image = option.querySelector("img[src]");
            if (image) {
              parsedOption.image_url = image.getAttribute("src");
              parsedOption.name = image.getAttribute("alt");
              if (!parsedOption.name) continue;
            } else parsedOption.name = option.textContent.trim();
          } catch (e) {
            parsedOption.name = option.textContent.trim();
          }

          const unavailable = option.querySelector(".a-button-unavailable");
          if (!unavailable) {
            parsedOption.available = true;
          }

          try {
            const isSelectedOption = option.querySelector(
              "span.a-button-selected"
            );
            if (isSelectedOption) {
              parsedOption.selectedOption = true;
            }
          } catch (e) {}
          console.log(parsedOption);
          options[key].push(parsedOption);
        }
      }
      return options;
    }
  );
  return options;
};

const parseAmazonDataOptionsOldClickOptions = async (optionList, page) => {
  const result = [];
  for (const option of optionList) {
    const parsedOption = await page.evaluate((option) => {
      const parsedOption = {};
      const url = option.getAttribute("data-defaultasin");
      parsedOption.url = url;
      try {
        const image = option.querySelector("img");
        if (image) {
          parsedOption.image_url = image.getAttribute("src");
          parsedOption.name = image.getAttribute("alt");
        } else {
          parsedOption.name = option
            .getAttribute("title")
            .trim()
            .match(/(?=Click to select ).*/)[0];
        }
      } catch (e) {
        parsedOption.name = option
          .getAttribute("title")
          .trim()
          .match(/(?=Click to select ).*/)[0];
      }
      if (option.classList.contains("swatchAvailable"))
        parsedOption.available = true;
      else parsedOption.available = false;

      try {
        const isSelectedOption = option.querySelector("span.a-button-selected");
        if (isSelectedOption) {
          parsedOption.selectedOption = true;
          parsedOption.available = true;
        }
      } catch (e) {}

      return parsedOption;
    }, option);
    result.push(parsedOption);
  }

  return result;
};

const parseAmazonDataOptionsOldDropdownMenu = async (key, page) => {
  const options = [];
  const dropdownOptionList = await page.$$(
    `select[name*="${key.toLowerCase()}"] > option:not([value^="-1"])`
  );

  for (const choice of dropdownOptionList) {
    const result = await page.evaluate((choice) => {
      const parsedOption = {};
      if (
        !choice.classList.contains("dropdownSelect") &&
        !choice.classList.contains("dropdownAvailable") &&
        !choice.classList.contains("dropdownUnavailable")
      )
        return null;

      const urlContainingText = choice.getAttribute("value");
      const regexSearchResult = urlContainingText.match(/[A-Z0-9]{2,}/);
      if (regexSearchResult.length >= 1) {
        parsedOption.url = regexSearchResult[0];
      }

      parsedOption.name = choice.textContent.trim();
      parsedOption.available =
        choice.classList.contains("dropdownSelect") ||
        choice.classList.contains("dropdownAvailable")
          ? true
          : false;
      if (choice.classList.contains("dropdownSelect"))
        parsedOption.selectedOption = true;

      return parsedOption;
    }, choice);

    if (!result) {
      continue;
    }
    options.push(result);
  }
  return options;
};

const fetchAmazonDataOptionsOld = async (page) => {
  const options = {};
  const foundOptions = await page.$$("form#twister > div");
  for (const option of foundOptions) {
    const key = await page.evaluate((elem) => {
      const keyText = elem
        .querySelector("label.a-form-label")
        .textContent.trim();
      return keyText.slice(0, -1);
    }, option);
    const isButtonList = await option.$$(
      "ul.a-button-list > li[data-defaultasin]"
    );
    if (isButtonList.length > 0) {
      options[key] = await parseAmazonDataOptionsOldClickOptions(
        isButtonList,
        page
      );
    } else {
      options[key] = await parseAmazonDataOptionsOldDropdownMenu(key, page);
    }
  }
  return options;
};

const fetchAmazonDataOptions = async (page) => {
  let options;
  try {
    const oldForm = await page.$("form#twister > div");
    /*
    await page.waitForSelector("form#twister > div", {
      timeout: 2000,
    });
    */
    if (oldForm) {
      console.log("Old Page!");
      options = await fetchAmazonDataOptionsOld(page);
    } else {
      console.log("New Page!");
      options = await fetchAmazonDataOptionsNew(page);
    }
  } catch (e) {
    console.log(e);
    console.log("New Page!");
    options = await fetchAmazonDataOptionsNew(page);
  }

  /*
  const pageSrcCode = await page.content();
  saveText("test.html", pageSrcCode);
  */

  return options;
};

function getBase64(url) {
  return axios
    .get(url, { responseType: "arraybuffer" })
    .then((response) =>
      Buffer.from(response.data, "binary").toString("base64")
    );
}

/*
 * The following function requires the deployment of the server that can solve the captcha
 * sent by Amazon. The server was implemented by combining the captcha program and the web
 * framework named "Flask" of Python.
 */
const solveCaptcha = async (page) => {
  // Check if the requested page is a captcha page
  const isCaptcha = await page.$("input#captchacharacters");
  if (!isCaptcha) return null;
  console.log("It is captcha!!!!!!");

  // A captcha comes in a form of a image, whose url is parsed and sent to the captcha
  // solving server.
  await page.waitForSelector("img");
  const url = await page.$eval("img", (elem) => elem.src);

  // Download and encode the binary of the image using base64, and then it is shipped to
  // the captcha solving server.
  const img_b64 = await getBase64(url);
  const { data } = await axios.post(
    "http://host.docker.internal:7777/solve",
    { captcha: img_b64 },
    { headers: { "Content-Type": "application/json" } }
  );
  // if the captcha isn't a string of six letters, the server has failed to solve the captcha.
  if (data.output.length != 6) return false;

  // Plug the solved captcha in to the input element and submit.
  console.log(`Extracted: ${data.output}`);
  await page.$eval(
    "input#captchacharacters",
    (elem, value) => {
      elem.value = value;
      return elem.value;
    },
    data.output
  );
  await page.click("button.a-button-text");

  // Wait until the redirect is complete, and decide whether the captcha is solved by looking for
  // the image of captcha in the web page.
  await page.waitForNavigation({ waitUntil: "load" });
  const isCaptchaAgain = await page.$("input#captchacharacters");
  if (isCaptchaAgain) {
    return false;
  }
  console.log("Captcha beaten!!!!!!!!!");
  return true;
};

module.exports = fetchAmazonData;
