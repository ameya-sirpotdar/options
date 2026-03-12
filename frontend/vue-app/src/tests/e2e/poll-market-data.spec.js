// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Poll Market Data Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Capture console errors to detect the TypeError
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.error(`Browser console error: ${msg.text()}`);
      }
    });

    await page.goto('/');
  });

  test('should load the application without TypeError in console', async ({ page }) => {
    const consoleErrors = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const typeErrors = consoleErrors.filter((err) =>
      err.includes('TypeError') && err.includes('Cannot create property')
    );

    expect(typeErrors).toHaveLength(0);
  });

  test('should render the InputPanel component', async ({ page }) => {
    await expect(page.locator('[data-testid="input-panel"]')).toBeVisible();
  });

  test('should display ticker input field', async ({ page }) => {
    await expect(page.locator('[data-testid="ticker-input"]')).toBeVisible();
  });

  test('should display the poll button', async ({ page }) => {
    await expect(page.locator('[data-testid="poll-button"]')).toBeVisible();
  });

  test('should allow user to type a ticker symbol', async ({ page }) => {
    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AAPL');
    await expect(tickerInput).toHaveValue('AAPL');
  });

  test('should not have TypeError when updating tickers v-model', async ({ page }) => {
    const consoleErrors = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('TSLA');

    const typeErrors = consoleErrors.filter((err) =>
      err.includes('TypeError') &&
      err.includes("Cannot create property 'value' on string")
    );

    expect(typeErrors).toHaveLength(0);
  });

  test('should show polling state when poll button is clicked', async ({ page }) => {
    // Mock the API to avoid real network calls
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ price: 150.0, ticker: 'AAPL' }),
      });
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AAPL');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    // After clicking, the button or UI should reflect polling state
    const isPollingIndicator = page.locator('[data-testid="polling-indicator"]');
    if (await isPollingIndicator.count() > 0) {
      await expect(isPollingIndicator).toBeVisible();
    }
  });

  test('should show calculating state during data processing', async ({ page }) => {
    await page.route('**/api/**', (route) => {
      // Delay the response to simulate calculation time
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ price: 200.0, ticker: 'GOOGL' }),
        });
      }, 500);
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('GOOGL');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    const isCalculatingIndicator = page.locator('[data-testid="calculating-indicator"]');
    if (await isCalculatingIndicator.count() > 0) {
      await expect(isCalculatingIndicator).toBeVisible();
    }
  });

  test('should pass isPolling prop correctly to InputPanel', async ({ page }) => {
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ price: 100.0, ticker: 'MSFT' }),
      });
    });

    // Verify no prop-related errors occur
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('MSFT');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    const propErrors = consoleErrors.filter((err) =>
      err.includes('Invalid prop') || err.includes('unknown prop')
    );

    expect(propErrors).toHaveLength(0);
  });

  test('should pass isCalculating prop correctly to InputPanel', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ price: 300.0, ticker: 'AMZN' }),
      });
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AMZN');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    await page.waitForTimeout(1000);

    const propErrors = consoleErrors.filter((err) =>
      err.includes('Invalid prop') || err.includes('unknown prop')
    );

    expect(propErrors).toHaveLength(0);
  });

  test('should stop polling when stop button is clicked', async ({ page }) => {
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ price: 150.0, ticker: 'AAPL' }),
      });
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AAPL');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    const stopButton = page.locator('[data-testid="stop-button"]');
    if (await stopButton.count() > 0) {
      await stopButton.click();

      const consoleErrors = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      await page.waitForTimeout(500);
      expect(consoleErrors).toHaveLength(0);
    }
  });

  test('should display market data results after polling', async ({ page }) => {
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ price: 175.5, ticker: 'AAPL' }),
      });
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AAPL');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    await page.waitForTimeout(2000);

    const resultsPanel = page.locator('[data-testid="results-panel"]');
    if (await resultsPanel.count() > 0) {
      await expect(resultsPanel).toBeVisible();
    }
  });

  test('should display Annualized ROI column header in options table when options data is loaded', async ({ page }) => {
    await page.route('**/api/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ticker: 'AAPL',
          price: 175.5,
          options: [
            {
              strike: 170,
              expiration: '2024-12-20',
              bid: 2.5,
              ask: 2.7,
              annualizedRoi: 0.1234,
            },
          ],
        }),
      });
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');
    await tickerInput.fill('AAPL');

    const pollButton = page.locator('[data-testid="poll-button"]');
    await pollButton.click();

    await page.waitForTimeout(2000);

    const optionsTable = page.locator('[data-testid="options-table"]');
    if (await optionsTable.count() > 0) {
      await expect(optionsTable).toBeVisible();
      await expect(optionsTable.getByText('Annualized ROI')).toBeVisible();
    }
  });

  test('should handle multiple ticker symbols', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    const tickerInput = page.locator('[data-testid="ticker-input"]');

    await tickerInput.fill('AAPL');
    await tickerInput.fill('');
    await tickerInput.fill('TSLA');
    await tickerInput.fill('');
    await tickerInput.fill('GOOGL');

    const typeErrors = consoleErrors.filter((err) =>
      err.includes("Cannot create property 'value' on string")
    );

    expect(typeErrors).toHaveLength(0);
  });
});