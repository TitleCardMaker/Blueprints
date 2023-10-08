from re import sub as re_sub, IGNORECASE


PATH_SAFE_TRANSLATION = str.maketrans({
    '?': '!',
    '<': '',
    '>': '',
    ':':' -',
    '"': '',
    '|': '',
    '*': '-',
    '/': '+',
    '\\': '+',
})


def get_blueprint_folders(series_name: str) -> tuple[str, str]:
    """
    Get the path-safe name for the given Series name.

    >>> get_blueprint_folders('The Expanse (2015)')
    ('E', 'The Expanse (2015)')
    >>> get_blueprint_folders('Demon Slayer: Kimetsu no Yaiba (2018)')
    ('D', 'Demon Slayer - Kimetsu no Yaiba (2018)')

    Args:
        series_name: Name of the Series.

    Returns:
        Tuple of the parent letter subfolder and the Path-safe name with
        prefix a/an/the and any illegal characters removed.
    """

    clean_name = str(series_name).translate(PATH_SAFE_TRANSLATION)
    sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

    return sort_name[0].upper(), clean_name
