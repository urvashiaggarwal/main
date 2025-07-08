const { execSync } = require("child_process")
const fs = require("fs")
const path = require("path")

console.log(" Diagnosing Selenium/Chrome setup...\n")

// Check Node.js version
console.log("1️ Node.js Version:")
console.log(`   ${process.version}`)

// Check Chrome browser installation
console.log("\n2️ Chrome Browser:")
try {
  let chromeVersion = ""

  if (process.platform === "win32") {
    // Windows - try multiple methods
    try {
      const output = execSync('reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version', {
        encoding: "utf8",
        stdio: "pipe",
      })
      chromeVersion = output.match(/version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)/)?.[1] || ""
    } catch {
      try {
        const output = execSync('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --version', {
          encoding: "utf8",
          stdio: "pipe",
        })
        chromeVersion = output.match(/Chrome (\d+\.\d+\.\d+\.\d+)/)?.[1] || ""
      } catch {
        try {
          const output = execSync('"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" --version', {
            encoding: "utf8",
            stdio: "pipe",
          })
          chromeVersion = output.match(/Chrome (\d+\.\d+\.\d+\.\d+)/)?.[1] || ""
        } catch {
          chromeVersion = "Not found"
        }
      }
    }
  } else if (process.platform === "darwin") {
    // macOS
    const output = execSync("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version", {
      encoding: "utf8",
      stdio: "pipe",
    })
    chromeVersion = output.match(/Chrome (\d+\.\d+\.\d+\.\d+)/)?.[1] || ""
  } else {
    // Linux
    const output = execSync("google-chrome --version || chromium-browser --version", {
      encoding: "utf8",
      stdio: "pipe",
    })
    chromeVersion =
      output.match(/Chrome (\d+\.\d+\.\d+\.\d+)|Chromium (\d+\.\d+\.\d+\.\d+)/)?.[1] ||
      output.match(/Chrome (\d+\.\d+\.\d+\.\d+)|Chromium (\d+\.\d+\.\d+\.\d+)/)?.[2] ||
      ""
  }

  if (chromeVersion && chromeVersion !== "Not found") {
    console.log(`    Chrome ${chromeVersion} found`)
  } else {
    console.log(`    Chrome not found or not accessible`)
    console.log(`    Install Chrome from: https://www.google.com/chrome/`)
  }
} catch (error) {
  console.log(`    Chrome check failed: ${error.message}`)
}

// Check ChromeDriver installation
console.log("\n3️ ChromeDriver:")
try {
  // Check if chromedriver is in node_modules
  const chromedriverPath = path.join(process.cwd(), "node_modules", "chromedriver")
  if (fs.existsSync(chromedriverPath)) {
    console.log(`    ChromeDriver package found in node_modules`)

    // Try to get version
    try {
      const chromedriverBin =
        process.platform === "win32"
          ? path.join(chromedriverPath, "lib", "chromedriver", "chromedriver.exe")
          : path.join(chromedriverPath, "lib", "chromedriver", "chromedriver")

      if (fs.existsSync(chromedriverBin)) {
        const output = execSync(`"${chromedriverBin}" --version`, { encoding: "utf8", stdio: "pipe" })
        console.log(`    ${output.trim()}`)
      } else {
        console.log(`    ChromeDriver binary not found at expected location`)
      }
    } catch (error) {
      console.log(`    ChromeDriver version check failed: ${error.message}`)
    }
  } else {
    console.log(`    ChromeDriver package not installed`)
    console.log(`    Run: npm install chromedriver`)
  }
} catch (error) {
  console.log(`    ChromeDriver check failed: ${error.message}`)
}

// Check selenium-webdriver
console.log("\n4️ Selenium WebDriver:")
try {
  const seleniumPath = path.join(process.cwd(), "node_modules", "selenium-webdriver")
  if (fs.existsSync(seleniumPath)) {
    const packageJson = JSON.parse(fs.readFileSync(path.join(seleniumPath, "package.json"), "utf8"))
    console.log(`    selenium-webdriver v${packageJson.version} installed`)
  } else {
    console.log(`    selenium-webdriver not installed`)
    console.log(`    Run: npm install selenium-webdriver`)
  }
} catch (error) {
  console.log(`    Selenium WebDriver check failed: ${error.message}`)
}

// Test basic Selenium functionality
console.log("\n5️ Selenium Test:")
try {
  const { Builder } = require("selenium-webdriver")
  const chrome = require("selenium-webdriver/chrome")

  console.log(`    Testing Chrome WebDriver initialization...`)

  const options = new chrome.Options()
  options.addArguments("--headless")
  options.addArguments("--no-sandbox")
  options.addArguments("--disable-dev-shm-usage")
  options.addArguments("--disable-gpu")

  const testSelenium = async () => {
    let driver
    try {
      driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build()
      console.log(`    Chrome WebDriver initialized successfully`)

      await driver.get("https://www.google.com")
      const title = await driver.getTitle()
      console.log(`    Successfully loaded page: ${title}`)

      await driver.quit()
      console.log(`    Selenium test completed successfully`)
    } catch (error) {
      console.log(`    Selenium test failed: ${error.message}`)
      if (driver) {
        try {
          await driver.quit()
        } catch {}
      }
    }
  }

  testSelenium()
} catch (error) {
  console.log(`    Selenium test setup failed: ${error.message}`)
}

console.log("\n" + "=".repeat(50))
console.log(" RECOMMENDATIONS:")
console.log("=".repeat(50))

console.log("\nIf Chrome is missing:")
console.log("• Download and install Chrome: https://www.google.com/chrome/")

console.log("\nIf ChromeDriver is missing:")
console.log("• Run: npm install chromedriver")
console.log("• Or run: npm install chromedriver@latest")

console.log("\nIf versions don't match:")
console.log("• Uninstall: npm uninstall chromedriver")
console.log("• Reinstall: npm install chromedriver@latest")

console.log("\nFor Windows users:")
console.log("• Make sure Chrome is installed in default location")
console.log("• Try running as Administrator if needed")

console.log("\nFor debugging:")
console.log("• Check Windows Defender/Antivirus isn't blocking")
console.log("• Ensure no corporate firewall restrictions")
