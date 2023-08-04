# update-flex

## update-flex.py usage

```
usage: update-flex.py [-h] [-l LANG] [-s SOURCE_CAWL_TYPE]
                      [-t TARGET_CAWL_TYPE] [-d]
                      [source_db] target_db [target_db ...]

Show or update FLEx database files in LIFT format.

positional arguments:
  source_db             The source file to get updates from.
  target_db             The target file(s) to be shown or updated.

optional arguments:
  -h, --help            show this help message and exit
  -l LANG, --lang LANG  The language whose text will be copied from the source
                        file(s). Defaults to the language of the 'lexical-
                        unit', but this can be used to specify a language from
                        the entry's glosses instead.
  -s SOURCE_CAWL_TYPE, --source-cawl-type SOURCE_CAWL_TYPE
                        The value used in the source's 'type' attribute to
                        designate a CAWL entry. [CAWL]
  -t TARGET_CAWL_TYPE, --target-cawl-type TARGET_CAWL_TYPE
                        The value used in the target's 'type' attribute to
                        designate a CAWL entry. [CAWL]
  -d, --debug
```

### LIFT - Lexical Interchange Format
A standard format developed and used by SIL for linguistic documentation.
https://github.com/sillsdev/lift-standard

### FLEx uses v0.13 as of 2022-03-18
https://github.com/sillsdev/lift-standard/blob/master/lift_13.pdf

> Window icon by VisualEditor team - https://git.wikimedia.org/summary/mediawiki%2Fextensions%2FVisualEditor.git, MIT, https://commons.wikimedia.org/w/index.php?curid=26927402
