const { execSync } = require("child_process")
const fs = require("fs")

console.log(" Setting up Selenium WebDriver with proper Chrome support...")

async function setupSelenium() {
  try {
    // Step 1: Check Chrome version
    console.log("\n1️ Checking Chrome browser version...")

    let chromeVersion = ""
    try {
      if (process.platform === "win32") {
        // Windows
        const output = execSync('reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version', {
          encoding: "utf8",
          stdio: "pipe",
        })
        chromeVersion = output.match(/version\s+REG_SZ\s+(\d+)/)?.[1] || ""
      } else if (process.platform === "darwin") {
        // macOS
        const output = execSync("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version", {
          encoding: "utf8",
          stdio: "pipe",
        })
        chromeVersion = output.match(/Chrome (\d+)/)?.[1] || ""
      } else {
        // Linux
        const output = execSync("google-chrome --version || chromium-browser --version", {
          encoding: "utf8",
          stdio: "pipe",
        })
        chromeVersion =
          output.match(/Chrome (\d+)|Chromium (\d+)/)?.[1] || output.match(/Chrome (\d+)|Chromium (\d+)/)?.[2] || ""
      }

      if (chromeVersion) {
        console.log(` Found Chrome version: ${chromeVersion}`)
      } else {
        throw new Error("Could not detect Chrome version")
      }
    } catch (error) {
      console.log(" Chrome browser not found or version detection failed")
      console.log("Please install Chrome browser from: https://www.google.com/chrome/")
      return
    }

    // Step 2: Install matching ChromeDriver
    console.log("\n2️ Installing matching ChromeDriver...")

    try {
      // Remove existing chromedriver
      execSync("npm uninstall chromedriver", { stdio: "inherit" })
    } catch (e) {
      // Ignore if not installed
    }

    // Install matching version
    const chromedriverVersion = `${chromeVersion}.0.0`
    console.log(`Installing chromedriver@${chromedriverVersion}...`)

    try {
      execSync(`npm install chromedriver@${chromedriverVersion}`, { stdio: "inherit" })
      console.log(` ChromeDriver ${chromedriverVersion} installed successfully`)
    } catch (error) {
      console.log(` Exact version not available, trying latest ${chromeVersion}.x.x...`)
      execSync(`npm install chromedriver@^${chromeVersion}.0.0`, { stdio: "inherit" })
    }

    // Step 3: Test Selenium setup
    console.log("\n3️ Testing Selenium WebDriver...")

    const { Builder } = require("selenium-webdriver")
    const chrome = require("selenium-webdriver/chrome")

    const options = new chrome.Options()
    options.addArguments("--headless")
    options.addArguments("--no-sandbox")
    options.addArguments("--disable-dev-shm-usage")
    options.addArguments("--disable-gpu")

    const driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build()

    await driver.get("https://www.google.com")
    const title = await driver.getTitle()
    await driver.quit()

    if (title.includes("Google")) {
      console.log(" Selenium WebDriver test successful!")
      console.log(" Your POI extraction with Selenium should now work!")
    } else {
      throw new Error("Test failed - could not load Google")
    }
  } catch (error) {
    console.log(" Selenium setup failed:", error.message)
    console.log("\n Manual steps to fix:")
    console.log("1. Install Chrome browser: https://www.google.com/chrome/")
    console.log("2. Run: npm install chromedriver")
    console.log("3. Restart your application")
    console.log("\n The app will still work for non-Selenium categories!")
  }
}

setupSelenium()
