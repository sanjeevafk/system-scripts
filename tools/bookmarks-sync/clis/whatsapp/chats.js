import { cli, Strategy } from '@jackwener/opencli/registry';
import { AuthRequiredError } from '@jackwener/opencli/errors';

const WHATSAPP_URL = 'https://web.whatsapp.com';
const WHATSAPP_DOMAIN = 'web.whatsapp.com';

cli({
  site: 'whatsapp',
  name: 'chats',
  access: 'read',
  description: 'List recent conversations from WhatsApp Web',
  domain: WHATSAPP_DOMAIN,
  strategy: Strategy.COOKIE,
  browser: true,
  args: [
    { name: 'limit', type: 'int', default: 20, help: 'Maximum chats to return' },
  ],
  columns: [
    'rank',
    'chat_name',
    'unread',
    'last_message',
    'time',
  ],
  func: async (page, kwargs) => {
    const limit = kwargs.limit || 20;

    await page.goto(WHATSAPP_URL);
    await page.wait(5);

    const isQrScreen = await page.evaluate(() => {
      return !!document.querySelector('canvas[aria-label*="Scan me"], div[data-ref]');
    });

    if (isQrScreen) {
      throw new AuthRequiredError(WHATSAPP_DOMAIN, 'WhatsApp Web requires authentication. Please scan QR code in Chrome.');
    }

    const chats = await page.evaluate((maxLimit) => {
      const rows = Array.from(document.querySelectorAll('#pane-side [role="row"], #pane-side [role="listitem"], div[data-testid="cell-frame-container"]'));
      const list = [];

      for (const row of rows) {
        const nameEl = row.querySelector('span[title], span[dir="auto"]._ao3e, span[dir="auto"]');
        const name = nameEl ? (nameEl.getAttribute('title') || nameEl.innerText.trim()) : 'Unknown';

        const badge = row.querySelector('[aria-label*="unread"], span[data-icon="unread-count"], span._aou8');
        const isUnread = !!badge;

        const msgEl = row.querySelector('span._ao3v, span[title][dir="ltr"], span.selectable-text');
        const lastMsg = msgEl ? msgEl.innerText.trim() : '';

        const timeEl = row.querySelector('div._ak8i, span._ak8i, time');
        const timeText = timeEl ? timeEl.innerText.trim() : '';

        list.push({
          chat_name: name,
          unread: isUnread ? 'Yes' : 'No',
          last_message: lastMsg,
          time: timeText
        });
      }

      return list.slice(0, maxLimit);
    }, limit);

    return chats.map((c, index) => ({
      rank: index + 1,
      chat_name: c.chat_name,
      unread: c.unread,
      last_message: c.last_message,
      time: c.time
    }));
  }
});
