#!/usr/bin/env node
const fs = require('fs');

let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);

  try {
    const data = JSON.parse(input);
    let model = data.model?.display_name || 'Gemini 3.5 Flash';
    const effort = data.model?.effort || data.effort || 'medium';
    
    // Strip redundant effort indicators from model name (e.g. "Gemini 3.5 Flash (Medium)")
    model = model.replace(/\s*\((Medium|High|Low)\)/i, '');

    const remaining = data.context_window?.remaining_percentage;
    const usedPercentage = data.context_window?.used_percentage;
    
    // Extract tokens - total_input_tokens represents the active loaded context window
    const tokensTotal = data.context_window?.context_window_size || data.context_window?.tokens_total;
    const tokensUsed = data.context_window?.total_input_tokens || data.context_window?.tokens_used || 0;

    let ctxStr = '';
    if (remaining != null || usedPercentage != null) {
      const usedPct = usedPercentage != null 
        ? Math.round(usedPercentage) 
        : Math.max(0, Math.min(100, Math.round(100 - remaining)));
      
      let color = '\x1b[32m'; // Green
      if (usedPct >= 75) {
        color = '\x1b[31m'; // Red
      } else if (usedPct >= 50) {
        color = '\x1b[33m'; // Yellow
      }

      ctxStr = ` │ Context: ${color}${usedPct}%\x1b[0m`;
      if (tokensUsed > 0 && tokensTotal > 0) {
        const usedK = (tokensUsed / 1000).toFixed(1);
        const totalK = (tokensTotal / 1000).toFixed(0);
        ctxStr += ` (${usedK}k/${totalK}k)`;
      }
    }

    process.stdout.write(`${model} · ${effort}${ctxStr}`);
  } catch (e) {
    process.stdout.write('Gemini 3.5 Flash · medium');
  }
});
