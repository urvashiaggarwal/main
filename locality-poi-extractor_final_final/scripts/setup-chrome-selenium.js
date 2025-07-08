const { execSync } = require("child_process")
const fs = require("fs")

console.log(" Setting up Chrome and Selenium for POI extraction...\n")

async function setupChromeSelenium() {
  try {
    // Step 1: Check if Chrome is installed
    console.log(" Checking Chrome installation...")

    let chromeFound = false
    try {
      if (process.platform === "win32") {
        execSync('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --version', { stdio: "pipe" })
        chromeFound = true
      } else if (process.platform === "darwin") {
        execSync("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version", { stdio: "pipe" })
        chromeFound = true
      } else {
        execSync("google-chrome --version", { stdio: "pipe" })
        chromeFound = true
      }
      console.log("    Chrome browser found")
    } catch (error) {
      console.log("    Chrome browser not found")
      console.log("    Please install Chrome from: https://www.google.com/chrome/")
      console.log("     Setup paused - install Chrome and run this script again")
      return
    }

    // Step 2: Install/Update ChromeDriver
    console.log("\n2️ Installing ChromeDriver...")

    try {
      // Remove existing chromedriver if present
      try {
        execSync("npm uninstall chromedriver", { stdio: "inherit" })
        console.log("     Removed existing ChromeDriver")
      } catch {
        // Ignore if not installed
      }

      // Install latest chromedriver
      console.log("    Installing ChromeDriver...")
      execSync("npm install chromedriver@latest", { stdio: "inherit" })
      console.log("   ChromeDriver installed successfully")
    } catch (error) {
      console.log("    ChromeDriver installation failed:", error.message)
      console.log("    Try running: npm install chromedriver --force")
      return
    }

    // Step 3: Test Selenium setup
    console.log("\n3️ Testing Selenium setup...")

    try {
      const { Builder } = require("selenium-webdriver")
      const chrome = require("selenium-webdriver/chrome")

      const options = new chrome.Options()
      options.addArguments("--headless")
      options.addArguments("--no-sandbox")
      options.addArguments("--disable-dev-shm-usage")

      console.log("    Creating test WebDriver...")
      const driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build()

      console.log("    Testing navigation...")
      await driver.get("https://www.google.com")
      const title = await driver.getTitle()

      await driver.quit()

      if (title.includes("Google")) {
        console.log("    Selenium test successful!")
        console.log("\n Setup completed successfully!")
        console.log(" Your POI extraction with Selenium should now work!")
      } else {
        throw new Error("Test navigation failed")
      }
    } catch (error) {
      console.log("    Selenium test failed:", error.message)
      console.log("\n Troubleshooting steps:")
      console.log("   • Run: node scripts/diagnose-selenium.js")
      console.log("   • Check if antivirus is blocking Chrome/ChromeDriver")
      console.log("   • Try running as Administrator (Windows)")
      console.log("   • Restart your terminal/IDE")
    }
  } catch (error) {
    console.log(" Setup failed:", error.message)
    console.log("\n Manual steps:")
    console.log("1. Install Chrome: https://www.google.com/chrome/")
    console.log("2. Run: npm install chromedriver")
    console.log("3. Run: node scripts/diagnose-selenium.js")
  }
}

setupChromeSelenium()
