import sys

from pathlib import Path


def get_outfile_object(old_file_obj, lang, debug):
    new_file_name = f"{old_file_obj.stem}_updated-{lang}.lift"
    new_file_obj = old_file_obj.with_name(new_file_name)
    if debug:
        print(f"DEBUG: {str(new_file_obj) = }")
    return new_file_obj

def get_unicode(text):
    unicode = "".join(map(lambda c: rf"\u{ord(c):04x}", text))
    return unicode

def verify_venv(debug):
    bin_dir = Path(sys.prefix)
    if debug:
        print(f"DEBUG: {bin_dir = }")
    if bin_dir.name == 'usr':
        script_dir = Path(__file__).parent
        env_full_path = script_dir.resolve() / 'env'
        if debug:
            print(f"DEBUG: {env_full_path = }")
        if env_full_path.is_dir():
            activate_path = env_full_path / 'bin' / 'activate'
        else:
            print(f"ERROR: Virtual environment not found at \"{env_full_path}\"")
            exit(1)
        # Virtual environment not activated.
        print("ERROR: Need to activate virtual environment:")
        print(f"$ . {activate_path}")
        exit(1)
