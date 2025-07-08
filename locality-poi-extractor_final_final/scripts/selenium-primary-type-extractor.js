const { Builder, By, until } = require("selenium-webdriver")
const chrome = require("selenium-webdriver/chrome")
const fs = require("fs")

async function extractPrimaryTypes() {
  // Read input data from file
  const inputFile = process.argv[2]
  const outputFile = process.argv[3]
  const xpath = process.argv[4] || "//div[contains(@class, 'fontBodyMedium') and contains(@aria-label, 'Category')]"

  if (!inputFile || !outputFile) {
    console.error("Usage: node selenium-primary-type-extractor.js <input-file> <output-file> [xpath]")
    process.exit(1)
  }

  let pois
  try {
    const inputData = fs.readFileSync(inputFile, "utf8")
    pois = JSON.parse(inputData)
    console.log(` Loaded ${pois.length} POIs for processing`)
  } catch (error) {
    console.error(" Error reading input file:", error.message)
    process.exit(1)
  }

  // Chrome options for better compatibility
  const options = new chrome.Options()
  options.addArguments("--headless")
  options.addArguments("--no-sandbox")
  options.addArguments("--disable-dev-shm-usage")
  options.addArguments("--disable-gpu")
  options.addArguments("--disable-web-security")
  options.addArguments("--disable-features=VizDisplayCompositor")
  options.addArguments("--window-size=1920,1080")
  options.addArguments("--disable-blink-features=AutomationControlled")
  options.addArguments("--disable-extensions")
  options.addArguments(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
  )

  console.log(" Initializing Chrome WebDriver for primary type extraction...")
  console.log(` XPath: ${xpath}`)

  let driver
  const primaryTypes = []

  try {
    // Build driver with options
    console.log(" Starting Chrome WebDriver...")
    driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build()
    console.log(" Chrome WebDriver initialized successfully")

    // Test basic functionality
    console.log(" Testing basic navigation...")
    await driver.get("https://www.google.com")
    const testTitle = await driver.getTitle()
    console.log(` Test navigation successful: ${testTitle}`)

    // Process each POI
    for (let i = 0; i < pois.length; i++) {
      const poi = pois[i]
      try {
        console.log(` Processing POI ${i + 1}/${pois.length}: ${poi.name}`)
        console.log(` URL: ${poi.google_map_url}`)

        // Navigate to Google Maps URL
        await driver.get(poi.google_map_url)

        // Wait for page to load
        console.log(" Waiting for page to load...")
        await driver.sleep(3000)

        // Try to find the element with the provided xpath
        console.log(" Looking for primary type element...")
        const element = await driver.wait(until.elementLocated(By.xpath(xpath)), 15000)
        const text = await element.getText()

        const primaryType = text.trim() || "not found"
        primaryTypes.push(primaryType)
        console.log(` Found primary type: "${primaryType}"`)

        // Small delay between requests
        await driver.sleep(2000)
      } catch (elementError) {
        console.log(` Could not extract primary type for ${poi.name}:`)
        console.log(`   Error: ${elementError.message}`)

        // Try to get page source for debugging
        try {
          const currentUrl = await driver.getCurrentUrl()
          console.log(`   Current URL: ${currentUrl}`)

          // Check if page loaded properly
          const pageTitle = await driver.getTitle()
          console.log(`   Page title: ${pageTitle}`)
        } catch (debugError) {
          console.log(`   Debug info failed: ${debugError.message}`)
        }

        primaryTypes.push("not found")
      }
    }

    // Write results to output file
    fs.writeFileSync(outputFile, JSON.stringify(primaryTypes, null, 2))
    console.log(` Primary types extracted and saved to ${outputFile}`)
    console.log(
      ` Results: ${primaryTypes.filter((t) => t !== "not found" && t !== "extraction failed").length}/${primaryTypes.length} successful`,
    )
  } catch (error) {
    console.error(" Selenium extraction failed:")
    console.error(`   Error type: ${error.name}`)
    console.error(`   Error message: ${error.message}`)

    if (error.message.includes("ChromeDriver")) {
      console.error("\n ChromeDriver Issues:")
      console.error("   • Make sure Chrome browser is installed")
      console.error("   • Run: npm install chromedriver")
      console.error("   • Check Chrome and ChromeDriver versions match")
    }

    if (error.message.includes("selenium-manager")) {
      console.error("\n Selenium Manager Issues:")
      console.error("   • This might be a Next.js server environment issue")
      console.error("   • Try running the diagnostic script: node scripts/diagnose-selenium.js")
    }

    // Write fallback results on failure
    const fallbackResults = pois.map(() => "extraction failed")
    fs.writeFileSync(outputFile, JSON.stringify(fallbackResults, null, 2))
    console.log(`📝 Wrote fallback results to ${outputFile}`)
  } finally {
    // Always quit the driver
    if (driver) {
      try {
        await driver.quit()
        console.log(" Chrome WebDriver closed successfully")
      } catch (quitError) {
        console.log(` Error closing WebDriver: ${quitError.message}`)
      }
    }
  }
}

// Handle unhandled promise rejections
process.on("unhandledRejection", (reason, promise) => {
  console.error(" Unhandled Rejection at:", promise, "reason:", reason)
  process.exit(1)
})

extractPrimaryTypes().catch((error) => {
  console.error(" Script execution failed:", error)
  process.exit(1)
})
