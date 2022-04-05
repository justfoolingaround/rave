def linguistic_expansion(*content, separator=", ", use_before_last=False, final="and"):
    """
    `a, b, c` -> `a, b and c.`
    """
    *r, l = content
    joined = separator.join(r)
    if use_before_last:
        joined += separator.strip()

    if l:
        joined += " {} {}".format(final, l)
    return joined
