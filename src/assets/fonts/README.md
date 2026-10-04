`language-flags.ttf` is a 38 KiB subset of Google's Noto Color Emoji font,
renamed to BoostyLanguageFlags. It supplies the 🇬🇧 and 🇷🇺 emoji in the
language picker, including in offline web builds. Flet registers it as
`LanguageFlags`; the picker uses it as a fallback for both the selected value
and menu items.

Source: https://github.com/googlefonts/noto-emoji/blob/main/2D/fonts/NotoColorEmoji.ttf
License: SIL Open Font License 1.1 (see OFL.txt).

The subset was generated with fontTools 4.66.1, populating the subset with
`🇬🇧🇷🇺`, retaining the GSUB ligatures and all name records. Name IDs 1, 3,
4, 6, and 16 were changed to `BoostyLanguageFlags`. When adding another flag,
regenerate the subset from the source font with the full list of flag emoji.
