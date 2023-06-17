async function fetchAmazonData(browser, url) {
	const data = {};
	const page = await browser.newPage();
	await page.goto(url);

	console.log(`Page Accessed: ${url}`);
	
	await page.waitForSelector("span#productTitle");
	try {
		const productName = await page.$eval("span#productTitle", title => title.textContent);
		data.productName = productName.trim();
	} catch (err) {
		data.productName = "undefined"
	}

	try {
		const price = await page.$eval(".a-price .a-offscreen", price => price.textContent);
		data.price = price.trim();
	} catch (err) {
		data.price = "undefined";
	}

	try {
		const imageurl = await page.$eval('div.a-carousel-viewport img', image => image.src);
		data.imageurl = imageurl;
	} catch (err) {
		data.imageurl = "undefined";
	}

	try {
		const rating = await page.$eval('#averageCustomerReviews a span', review => review.textContent);
		data.rating = rating.trim();
	} catch (err) {
		data.rating = "undefined";
	}

	try {
		const brand = await page.$eval("a#bylineInfo", brand => brand.textContent);
		data.brand = brand.trim();
	} catch (err) {
		data.brand = "undefined";
	}

	data.options = await fetchAmazonDataOptions(page);
	page.close();
	return data 
}

const fetchAmazonDataOptions = async (page) => {
	const data = [];
	const options_candidate = await page.$$("form#twister > div");
	for (const candidate of options_candidate) {
		const hasDropMenu = await candidate.$('select[name="dropdown_selected_size_name"]');
		if (hasDropMenu) {
			const options = await parseDropDownOptions(candidate);
			data.push(options);
		} else {
			const options = await parseClickOptions(candidate);
			data.push(options);
		}
		
	}
	
	return data;
};

const parseDropDownOptions = async (elemHandle) => {
	const options = await elemHandle.$eval('select[name="dropdown_selected_size_name"]', elem => {
		const result = [];
		result.push(elem.getAttribute("data-a-touch-header"));
		const choices = elem.children;

		for (const choice of choices) {
			obj = {}
			if (choice === choices.item(0)) continue;
			obj.name = choice.textContent.trim();
			obj.url = choice.getAttribute("value");
			obj.available = choice.classList.contains("dropdownAvailable") ? true : false;
			result.push(obj);
		}

		return result;
	});
	
	return options;
};

const parseClickOptions = async (elemHandle) => {
	try {
		const options = await elemHandle.$eval('ul', elem => {
			const result = [];
			const choices = elem.children;

			for (const choice of choices) {
				obj = {}
				obj.name = choice.title;
				obj.url = choice.getAttribute("data-dp-url");
				obj.available = choice.classList.contains("swatchUnavailable") ? false : true;
				result.push(obj);
			}

			return result;
		});
		
		const label = await elemHandle.$eval(".a-row", elem => {
			return elem.firstElementChild.textContent;
		});
		
		options.unshift(label.trim());
		return options;
	} catch (err) {
		return [];
	}
};
/*
const fetchAmazonDataOptionsDropdown = async (page) => {
	const options = await page.$("div.a-popover ul");
	if (!options) return null;
	const arr = await options.evaluate((elem) => {
		const temp_arr = [];
		const choices = elem.children;

		for (const choice of choices) {
			const obj = {};
			if (choice == choices.item(0)) continue;
			obj.id = choice.id;
			obj.url = choice.firstElementChild.getAttribute("data-value");
			obj.title = choice.firstElementChild.textContent;

			temp_arr.push(obj);
		}

		return temp_arr;
	});

	return arr;
}
*/
module.exports = fetchAmazonData;
