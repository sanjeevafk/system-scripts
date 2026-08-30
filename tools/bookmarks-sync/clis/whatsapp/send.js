import { cli, Strategy } from '@jackwener/opencli/registry';
import { ArgumentError, AuthRequiredError, CommandExecutionError } from '@jackwener/opencli/errors';

const WHATSAPP_URL = 'https://web.whatsapp.com';
const WHATSAPP_DOMAIN = 'web.whatsapp.com';

cli({
  site: 'whatsapp',
  name: 'send',
  access: 'write',
  description: 'Send a message to a contact or group on WhatsApp Web',
  domain: WHATSAPP_DOMAIN,
  strategy: Strategy.COOKIE,
  browser: true,
  args: [
    { name: 'recipient', type: 'string', required: true, help: 'Contact or group name exactly as it appears in WhatsApp' },
    { name: 'message', type: 'string', required: true, help: 'Message text to send' },
  ],
  columns: [
    'recipient',
    'status',
    'message',
    'timestamp'
  ],
  func: async (page, kwargs) => {
    const recipient = kwargs.recipient;
    const message = kwargs.message;

    if (!recipient || !message) {
      throw new ArgumentError('Both recipient and message are required.');
    }

    await page.goto(WHATSAPP_URL);
    await page.wait(5);

    const isQrScreen = await page.evaluate(() => {
      return !!document.querySelector('canvas[aria-label*="Scan me"], div[data-ref]');
    });

    if (isQrScreen) {
      throw new AuthRequiredError(WHATSAPP_DOMAIN, 'WhatsApp Web requires authentication. Please scan QR code in Chrome.');
    }

    // Step 1: Search for the contact in search bar
    const searchResult = await page.evaluate(async (targetName) => {
      const searchBox = document.querySelector('div[contenteditable="true"][data-tab="3"], div[role="textbox"][aria-label*="Search"]');
      if (!searchBox) return { error: 'Search box not found' };

      searchBox.focus();
      document.execCommand('insertText', false, targetName);
      searchBox.dispatchEvent(new Event('input', { bubbles: true }));

      return { searched: true };
    }, recipient);

    if (searchResult.error) {
      throw new CommandExecutionError(searchResult.error);
    }

    await page.wait(2);

    // Step 2: Click matching chat in search results
    const selectResult = await page.evaluate((targetName) => {
      const rows = Array.from(document.querySelectorAll('#pane-side [role="row"], #pane-side [role="listitem"], div[data-testid="cell-frame-container"]'));
      const targetRow = rows.find(r => {
        const titleEl = r.querySelector('span[title], span[dir="auto"]');
        const title = titleEl ? (titleEl.getAttribute('title') || titleEl.innerText.trim()) : '';
        return title.toLowerCase().includes(targetName.toLowerCase());
      });

      if (!targetRow) return { error: 'No matching contact or group found for: ' + targetName };

      targetRow.click();
      return { selected: true };
    }, recipient);

    if (selectResult.error) {
      throw new CommandExecutionError(selectResult.error);
    }

    await page.wait(2);

    // Step 3: Type message into active chat input and send
    const sendResult = await page.evaluate((msgText) => {
      const input = document.querySelector('footer div[contenteditable="true"], footer div[role="textbox"]');
      if (!input) return { error: 'Chat message input box not found' };

      input.focus();
      document.execCommand('insertText', false, msgText);
      input.dispatchEvent(new Event('input', { bubbles: true }));

      // Find send button
      const sendBtn = document.querySelector('button[aria-label*="Send"], span[data-icon="send"]')?.closest('button');
      if (sendBtn) {
        sendBtn.click();
        return { sent: true };
      }

      // Fallback: simulate Enter key
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
      return { sent: true, note: 'Enter dispatched' };
    }, message);

    if (sendResult.error) {
      throw new CommandExecutionError(sendResult.error);
    }

    return [{
      recipient: recipient,
      status: 'Sent',
      message: message,
      timestamp: new Date().toISOString()
    }];
  }
});
