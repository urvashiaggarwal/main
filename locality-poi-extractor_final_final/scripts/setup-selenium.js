const { execSync } = require("child_process")
const fs = require("fs")
const path = require("path")

console.log("Setting up Selenium WebDriver...")

try {
  // Check if Chrome is installed
  try {
    if (process.platform === "win32") {
      execSync("where chrome", { stdio: "ignore" })
    } else {
      execSync("which google-chrome || which chromium-browser", { stdio: "ignore" })
    }
    console.log("✓ Chrome browser found")
  } catch (error) {
    console.log("⚠ Chrome browser not found. Please install Chrome browser first.")
    console.log("Download from: https://www.google.com/chrome/")
  }

  // Install chromedriver
  console.log("Installing chromedriver...")
  execSync("npm install chromedriver --save", { stdio: "inherit" })
  console.log("✓ Chromedriver installed")

  // Test selenium setup
  console.log("Testing Selenium setup...")
  const { Builder } = require("selenium-webdriver")
  const chrome = require("selenium-webdriver/chrome")

  const options = new chrome.Options()
  options.addArguments("--headless")
  options.addArguments("--no-sandbox")
  options.addArguments("--disable-dev-shm-usage")

  const driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build()

  await driver.get("https://www.google.com")
  await driver.quit()

  console.log("✓ Selenium WebDriver setup successful!")
} catch (error) {
  console.log("⚠ Selenium setup failed:", error.message)
  console.log("The application will work without Selenium, but primary type extraction will be limited.")
  console.log("To fix this:")
  console.log("1. Install Chrome browser")
  console.log("2. Run: npm install chromedriver")
  console.log("3. Restart the application")
}
