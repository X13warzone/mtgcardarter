# MTG Card Arter
An applet for making printable sheets for proxying Magic the Gathering cards.

Still a WIP, and may have bugs or issues. If you find any, please let me know in the Issues tab.

Currently works with printing out A4 sheets with or without a margin, and handles Moxfield format decklist input and automatic Scryfall querying.

Note: It does take a while to run due to Scryfall's restriction on API overusage. Just let it run for a few minutes and it should be done (for 100ish cards)

Note: This applet completely ignores foils, since you can't print foiling onto basic printing paper. The program still works if the imported cards are marked as foil (such as with \*F\* like Moxfield), it will simply ignore the \*F\* part.

Notable variables/constants (if you want to change any):

- `PAGE_INCLUDE_EDGE_MARGIN`: Sets whether the printed sheet should include a width-ed margin. If set to true, then the resulting sheet will be A4 sized. If set to false, the resulting sheet will be slightly less than A4 sized, but will result in an A4 sized sheet if the printer requires a margin of some width.
- `mtgc.txt`: The input file used to query Scryfall.
- `OUT_DIR`: The folder to output images to.
- `IN_DIR`: If you have any custom images you want to use (i.e. custom cards, or non MTG cards like a floating mana tracker), put them in this folder.
***
## Known Issues:
- Empty
## To do:
- Check promo cards
- Check the list cards
- Custom image sizes
