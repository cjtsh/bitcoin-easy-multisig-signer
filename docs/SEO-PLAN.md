# Website SEO and sharing handoff

## Canonical site

- Homepage: https://bitcoineasysigner.com/
- User manual: https://bitcoineasysigner.com/user-manual.html
- Privacy notice: https://bitcoineasysigner.com/privacy.html
- Sitemap: https://bitcoineasysigner.com/sitemap.xml
- Crawler rules: https://bitcoineasysigner.com/robots.txt

The canonical host is the apex HTTPS domain. The pages declare canonical URLs, unique titles and descriptions, Open Graph metadata, and large X cards. The 1200 × 630 PNG share graphic is at `assets/social-card.png`. LinkedIn, WhatsApp, and Telegram generally read Open Graph previews; X reads the Twitter card fields. Share links are also provided on the homepage.

## Search intent and natural language

Focus the homepage on the product and audience rather than repeating a keyword list:

- Bitcoin multisig software for families and trusted helpers
- Bitcoin multisig user manual for spouses, trustees, and estate professionals
- open-source Bitcoin multisig signing app for macOS
- hardware wallet multisig transaction review
- helping a family member use an existing Bitcoin multisig wallet

The home page and manual use these phrases in titles, headings, descriptions, and visible explanatory text. Google does not use the `meta keywords` tag for web ranking, so no keyword-stuffing tag is included. Keep claims aligned with the documented wallet, device, network, and safety scope.

## Google Search Console handoff

1. Add the **Domain** property `bitcoineasysigner.com` in Google Search Console.
2. Copy the exact TXT verification record Google gives you and add it at the domain's DNS provider. Do not guess or reuse a verification token. Once DNS propagates, verify ownership.
3. Open the verified property, choose **Sitemaps**, enter `sitemap.xml`, and submit it.
4. Use **URL inspection** for the homepage and `/user-manual.html`; request indexing if available. Indexing and display timing are controlled by Google.
5. Return to Search Console's Page indexing and Performance reports after Google has crawled the pages.

Domain-property verification needs a DNS TXT record; this repo cannot create that record because the unique value comes from your Search Console account and DNS host. No analytics tracker is installed. Search Console provides search performance; if you also want visitor analytics later, decide on a privacy notice/consent approach before adding a third-party analytics tag.

## Maintenance

When page copy or site URLs change, update the matching canonical/social URL and sitemap. Keep share image dimensions at 1200 × 630 and check previews after deployment in each platform's share/debug tool. Share previews may be cached by social platforms.
