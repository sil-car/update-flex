# update-flex

## Usage

```
usage: update-flex.py [-h] [-g GLOSSES] [-i SOURCE_ID_TYPE]
                      [-I TARGET_ID_TYPE] [-s]
                      [source_db] [target_db [target_db ...]]

Show or update FLEx database files in LIFT format.

positional arguments:
  source_db             The source file to get updates from.
  target_db             The target file(s) to be shown or updated.

optional arguments:
  -h, --help            show this help message and exit
  -g GLOSSES, --glosses GLOSSES
                        Update glosses in target file(s) with given 
                        language(s) from source file. Defaults to the
                        language of the source file's 'lexical-unit', but
                        this can be used to specify a language from the
                        entry's glosses instead.
  -s SOURCE_ID_TYPE, --source-cawl-type SOURCE_CAWL_TYPE
                        The value used in the source's 'type' attribute to
                        designate a CAWL entry. [CAWL]
  -t TARGET_ID_TYPE, --target-cawl-type TARGET_CAWL_TYPE
                        The value used in the target's 'type' attribute to
                        designate a CAWL entry. [CAWL]
  -s, --semantic-domain
                        Update semantic domain info from source file to target
                        file(s).
```

## Run script from repo
```
update-flex$ . env/bin/activate
(env) update-flex$ python3 -c 'import update_flex.app; update_flex.app.main()' [ARGS]
```

### LIFT - Lexical Interchange Format
A standard format developed and used by SIL for linguistic documentation.
https://github.com/sillsdev/lift-standard

### FLEx uses v0.13 as of 2022-03-18
https://github.com/sillsdev/lift-standard/blob/master/lift_13.pdf

> Window icon by VisualEditor team - https://git.wikimedia.org/summary/mediawiki%2Fextensions%2FVisualEditor.git, MIT, https://commons.wikimedia.org/w/index.php?curid=26927402
