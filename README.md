# MTG Card Arter
An applet for making printable sheets for proxying Magic the Gathering cards.

Still a WIP, with quite a few bugs and issues to iron out.
Currently works with printing out A4 sheets with/without a margin, and handles file input and Scryfall querying.

Note: This applet completely ignores foils, since that's part of the printing process. It still works if the imported cards are marked as foil (such as with \*F\* like Moxfield), it just deletes the \*F\* part.

Notable variables/constants:

- `PAGE_INCLUDE_EDGE_MARGIN`: Sets whether the printed sheet should include a width-ed margin. If set to true, then the resulting sheet will be A4 sized. If set to false, the resulting sheet will be slightly less than A4 sized, but will result in an A4 sized sheet if the printer requires a margin of some width.
- `mtgc.txt`: The input file used to query Scryfall.
***
# Known Issues:
- `mtgc.txt`: Scryfall query errors with:
  - Promo cards
  - The List cards
  - Any cards with a letter in its collector number on Scryfall
  - Possibly some dual-faced or special cards. These have to be handled on a case-by-case basis, so if you find any issues with a card with a valid name, set and collector number, let me know.
