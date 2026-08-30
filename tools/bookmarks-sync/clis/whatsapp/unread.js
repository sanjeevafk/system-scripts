import { cli, Strategy } from '@jackwener/opencli/registry';
import { AuthRequiredError, EmptyResultError } from '@jackwener/opencli/errors';

const WHATSAPP_URL = 'https://web.whatsapp.com';
const WHATSAPP_DOMAIN = 'web.whatsapp.com';

cli({
  site: 'whatsapp',
  name: 'unread',
  access: 'read',
  description: 'List unread chats and recent message previews from WhatsApp Web',
  domain: WHATSAPP_DOMAIN,
  strategy: Strategy.COOKIE,
  browser: true,
  args: [
    { name: 'limit', type: 'int', default: 20, help: 'Maximum unread chats to return' },
  ],
  columns: [
    'rank',
    'chat_name',
    'unread_count',
    'last_message',
    'time',
  ],
  func: async (page, kwargs) => {
    const limit = kwargs.limit || 20;

    await page.goto(WHATSAPP_URL);
    await page.wait(5);

    const isQrScreen = await page.evaluate(() => {
      const qr = document.querySelector('canvas[aria-label*="Scan me"], div[data-ref]');
      return !!qr;
    });

    if (isQrScreen) {
      throw new AuthRequiredError(WHATSAPP_DOMAIN, 'WhatsApp Web requires authentication. Please scan QR code in Chrome.');
    }

    const chats = await page.evaluate((maxLimit) => {
      // Find chat rows
      const rows = Array.from(document.querySelectorAll('#pane-side [role="row"], #pane-side [role="listitem"], div[data-testid="cell-frame-container"]'));
      const unreadList = [];

      for (const row of rows) {
        // Look for unread badge
        const badge = row.querySelector('[aria-label*="unread"], span[data-icon="unread-count"], span._aou8, span[aria-label*="unread message"]');
        const badgeText = badge ? (badge.innerText || badge.getAttribute('aria-label') || '1') : '';
        const unreadCountMatch = badgeText.match(/\d+/);

        if (badge || unreadCountMatch) {
          const nameEl = row.querySelector('span[title], span[dir="auto"]._ao3e, span[dir="auto"]');
          const name = nameEl ? (nameEl.getAttribute('title') || nameEl.innerText.trim()) : 'Unknown';

          const msgEl = row.querySelector('span._ao3v, span[title][dir="ltr"], span.selectable-text');
          const lastMsg = msgEl ? msgEl.innerText.trim() : '';

          const timeEl = row.querySelector('div._ak8i, span._ak8i, time');
          const timeText = timeEl ? timeEl.innerText.trim() : '';

          unreadList.push({
            chat_name: name,
            unread_count: unreadCountMatch ? parseInt(unreadCountMatch[0], 10) : 1,
            last_message: lastMsg,
            time: timeText
          });
        }
      }

      return unreadList.slice(0, maxLimit);
    }, limit);

    return chats.map((c, index) => ({
      rank: index + 1,
      chat_name: c.chat_name,
      unread_count: c.unread_count,
      last_message: c.last_message,
      time: c.time
    }));
  }
});
