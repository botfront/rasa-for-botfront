import re
from rasa_addons.core.nlg.constants import NlgEnum

def rewrite_url(message: dict, url_substitution_pattern: list):
    """Rewrite image url with the pattern found in endpoint."""
    
    if url_substitution_pattern:
        if NlgEnum.IMAGE.value in message.keys():
            substitute(message, NlgEnum.IMAGE.value, url_substitution_pattern)
        elif NlgEnum.ELEMENTS.value in message.keys():
            for element in message[NlgEnum.ELEMENTS.value]:
                substitute(element, NlgEnum.IMAGE_URL.value, url_substitution_pattern)

def substitute(message: dict, key: str, url_substitution_pattern: list):
    """Substitute rewritten url."""

    url = message[key]
    for item in url_substitution_pattern:
        substitute = re.sub(item.get(NlgEnum.PATTERN.value), item.get(NlgEnum.REPLACEMENT.value), message[key])
        if substitute != url:
            message[key] = substitute
            return
    return