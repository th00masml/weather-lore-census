# Data licenses

## 1. Source (public domain)

Richard Inwards, *Weather Lore*, 3rd ed. (London: Elliot Stock, 1898).
Public domain in the US (published before 1929).
https://archive.org/details/weatherlorecolle00inwa
Proverb quotations reproduced under public domain.

## 2. Weather data (Open Government Licence v3)

- HadCET: daily mean Central England Temperature series, 1772-present.
  Met Office Hadley Centre observations datasets.
  https://www.metoffice.gov.uk/hadobs/hadcet/
- HadUKP (HadEWP): daily England & Wales precipitation, 1931-present.
  https://www.metoffice.gov.uk/hadobs/hadukp/

Both © Crown copyright, Met Office, released under the UK Open Government
Licence v3 (free reuse with attribution):
https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
Attribution: contains Met Office data © Crown copyright.

## 3. Models

`claude-sonnet-5` via the authenticated Claude CLI (`claude -p`), OAuth
session, no API key — used ONLY to formalise proverbs into rules (cached
in `outputs/`). The evaluation uses no model at all.

## Not committed

`data/raw/` (Inwards scan text, Met Office series) is gitignored;
all re-downloadable from the URLs above.
