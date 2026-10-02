# Search and sharing notes for Bitcoin Easy Signer

## Product description

Bitcoin Easy Signer is a free, open-source Mac application that helps a spouse, trustee, lawyer, accountant, or other trusted person make a payment from an existing supported Bitcoin multisig wallet. The wallet owner supplies one BSMS definition file and the required hardware signers. The app checks the public wallet identity and funding, prepares the payment, requests hardware signatures, verifies the signed transaction, and broadcasts only after a final review and explicit confirmation. It does not create a wallet, hold private keys, or recover seed words.

This is the source of truth for SEO and social copy. Do not describe the product as a wallet, wallet software, wallet creation, an inheritance service, or seed recovery. The supported scope is native SegWit multisig with two or three total keys; the threshold comes from the file. Do not imply that three signatures are always required.

## Pages and metadata

- Home: https://bitcoineasysigner.com/ — product and trusted-helper use case.
- User manual: https://bitcoineasysigner.com/user-manual.html — operator steps and limits.
- Privacy notice: https://bitcoineasysigner.com/privacy.html — website and app privacy.
- The homepage title and social copy describe *sending Bitcoin from an existing multisig wallet*. The visible homepage prose is preserved from before this metadata work.
- Each page has a canonical URL, a distinct description, Open Graph tags and an X large-image card. The share image is `assets/social-card-v3.png` (1200 × 630 PNG). LinkedIn, WhatsApp and Telegram can use the Open Graph tags; X can use its card tags. Share links on the homepage use the same factual language.

## Search topics

Use these phrases only where they answer a visitor's question in natural copy. They are search-intent hypotheses, not measured volumes or ranking promises.

- Brand: Bitcoin Easy Signer; Bitcoin Easy Signer user manual.
- Task: send Bitcoin from an existing multisig wallet; make a Bitcoin multisig payment with hardware signers.
- Workflow: use a BSMS wallet file to make a payment; review and sign a multisig Bitcoin transaction.
- Audience context: a spouse, trustee, lawyer, accountant or estate helper who needs to move Bitcoin from an existing wallet.

Do not target “multisig wallet software”, “create a multisig wallet”, or “recover a seed phrase”. Google does not use `meta keywords` for web ranking, so no keyword list is inserted into page metadata.

## Crawl and submission

- `robots.txt` allows the public site and points to `sitemap.xml`; the canonical HTML is available without login or client-side rendering. `llms.txt` is a compact, optional map for AI agents. It is an emerging convention, not an indexing guarantee. General crawler access does not guarantee inclusion in search or AI answers.
- The sitemap contains the three canonical HTML pages. Update it only for real page additions; do not invent `lastmod` timestamps.
- In Google Search Console, add the Domain property `bitcoineasysigner.com`, verify with the exact DNS TXT record Google supplies, submit `sitemap.xml`, and inspect the homepage and manual URLs. Search Console is distinct from Google Analytics. No analytics tracker is installed; the site's privacy notice says it does not use project-run analytics.
- After publishing a new card, inspect the live HTML and PNG. Social platforms may cache old previews; use their refresh tools where available and reshare the URL.

## Maintenance

When the public app version or its supported scope changes, align the download link, structured data, page metadata, card text and image, and manual. Make claims only where the current release evidence supports them.
