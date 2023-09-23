### ToDo

- [ ] Add a way to find the version number in the GUI window.
- [ ] Add tooltips to entry fields that give examples/explanation.

### Done.

- [x] Ensure desired gloss handling:
  - [x] In the general case, if a language's gloss already exists in the Target 
    file, it should be skipped if "Allow overwrite?" is unchecked or replaced if
    "Allow overwrite?" is checked.
  - [x] In the case where the Target gloss is in Sango the gloss should be
    replaced with the Lexical Unit text (and possibly any new Sango glosses)
    from the Source.
- [x] Ensure desired Semantic Domain handling: always overwrite from SD in Source.
- Add in deduplication:
  - [x] identical gloss entries from the same language. (haven't confirmed yet)
  - [x] terms within a single gloss entry.
  - [x] semantic domain entries.
